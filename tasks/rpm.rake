module RPM
  def self.rpm_name
    return Project[:PROJECT]
  end

  #
  # Determine the RPM version installed on the given hostclass
  # in the given environment.
  #
  # Returns an array of [rpm, version, build],
  # or nil.
  #
  def self.rpm_version(environment, hostclass=nil, rpm=nil)
    hostclass ||= Project[:HOSTCLASS]
    rpm ||= rpm_name
    command = "yum list installed #{rpm}"
    io = WGR.hostclass_command(hostclass, environment, [command])
    output = io.read
    if output.match(/Installed Packages\n([^\.]+)(?:\S+)\s+([\d\.]+)-(\d+)/)
      rpm, version, build = $1, $2, $3
      return [rpm, version, build]
    else
      return nil
    end
  end
end

namespace "rpm" do
  desc "Verify we have RPM environment variables and prerequisites"
  task :verify do
    notice("Verifying RPM prerequisites")
    wg_rpm_msg = <<-EOS
Set WG_RPMBUILD to the path to wg_rpmbuild.py.
To obtain wg_rpmbuild.py, clone the rpmtools repository:

git clone git://mcgit.mc.wgenhq.net/wgen/rpmtools
    EOS
    require_env('WG_RPMBUILD', wg_rpm_msg)
    require_env('WORKSPACE', 'Set WORKSPACE to the path to the egg directory.')
    require_env('CI_REPO', 'Set CI_REPO to the path to place the RPM.')
    require_env('BUILD_NUMBER', 'Set BUILD_NUMBER to the build number to use in the RPM.')
    rpmbuild = `which rpmbuild`.strip
    if rpmbuild.empty? then
      error(["rpmbuild not found",
             "Please install rpmbuild. See this document for details:",
             "http://goo.gl/sRFVmQ"])
    end
  end

  desc "Build an RPM"
  task :build => [:verify] do
    notice("Building RPM")
    version = Version.get_package_version
    repo_dir = ENV['CI_REPO']

    publish_files_to(repo_dir) do |tmpdir|
      sh "python $WG_RPMBUILD --dont-clean-staging --ignore-existing-staging -r $WORKSPACE -Dversion=#{version} -Dbuild_number=$BUILD_NUMBER -Dcheckoutroot=$WORKSPACE -o #{tmpdir} jenkins/#{Project[:PROJECT]}.spec" do |ok, err|
        error("Failed to build RPM") unless ok
      end
    end

    good("RPM built")
  end
end



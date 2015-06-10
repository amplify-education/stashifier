module Version

  def self.inject_variable(filename, flag, value)
    result = system 'tasks/version/inject_variable.py', flag, value, filename
    raise (lowlight("Version injection failed")) if not result
  end

  def self.inject_git_hash
    inject_variable(VERSION_FILE, '-g', get_git_hash)
  end

  def self.inject_rpm_version
    rpm_version = "#{get_package_version}-#{get_rpm_build}"
    inject_variable(VERSION_FILE, '-r', rpm_version)
  end

  def self.get_package_version
    Setup.get_package_version
  end

  def self.get_git_hash
    Git.get_current_hash
  end

  # Reads the RPM_BUILD environment variable if available
  def self.get_rpm_build
    ENV['RPM_BUILD'] or raise(lowlight("RPM_BUILD is not set"))
  end

  VERSION_FILE = "#{ProjectPaths::PACKAGE_DIR}/version.py"
end

namespace "version" do
  desc "Inject the current git hash into #{Version::VERSION_FILE}"
  task :inject_git do
    Version.inject_git_hash
  end

  desc "Inject the current RPM version and build into #{Version::VERSION_FILE}"
  task :inject_rpm do
    Version.inject_rpm_version
  end
end

require 'tmpdir'

module Setup
  def self.setup(cmd)
    sh "python setup.py #{cmd}"
  end

  def self.get_package_version
    version = `python -c 'import pkg_resources; print pkg_resources.require("#{Project[:PACKAGE]}")[0].version'`.strip
    raise("Couldn't determine the package version") if version.empty?
    return version
  end

  def self.installed_versions
    `pip freeze`
  end
end

namespace "setup" do
  desc "Install dependencies"
  task :install_deps => ["virtualenv:verify"] do
    notice("Installing dependencies")
    Pip.install "-r requirements.pip"
    notice("Dependencies installed")
  end

  desc "Install egg"
  task :install => ["install_deps"] do
    notice("Installing egg")
    Pip.install "-r requirements.pip"
    Setup.setup "install"
    notice("Egg installed")
    print Setup.installed_versions
  end

  desc "Install the egg in development mode"
  task :develop => ["install_deps"] do
    notice("Installing egg in development mode")
    Pip.install "-e ."
    Setup.setup "develop"
    notice("Egg installed in development mode.")
    print Setup.installed_versions
  end

  desc "Publish the egg to the Pynest"
  task :pynest => ["virtualenv:verify", "version:inject_git"] do
    notice("Publishing to pynest")
    require_env('PYNEST', ' - this is needed to publish the egg to the pynest directory')
    nest_dir = ENV['PYNEST']

    publish_files_to(nest_dir) do |tmpdir|
      Setup.setup %|sdist -d "#{tmpdir}"|
    end

    version = Setup.get_package_version
    good("Published egg version #{version} to pynest #{nest_dir}")
  end
end

include FileUtils

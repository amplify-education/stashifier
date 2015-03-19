module Version
  def self.var_regex(varname)
    /(#{varname}\s+=\s+[\"'])([^\"']*)([\"'])/
  end

  # Replaces the second group in the given regex
  # with the given value, on each line.
  def self.set_var_in_lines(lines, regex, value)
    lines.map {|line|
      line.gsub(regex, "\\1#{value}\\3")
    }
  end

  def self.inject_variable(filename, regex, value)
    lines = IO.readlines(filename)
    updated_lines = set_var_in_lines(lines, regex, value)
    File.open(filename, 'w') do |f|
      f.puts updated_lines
    end
  end

  def self.inject_git_hash
    inject_variable(VERSION_FILE, GIT_HASH_REGEX, get_git_hash)
  end

  def self.inject_rpm_version
    rpm_version = "#{get_package_version}-#{get_rpm_build}"
    inject_variable(VERSION_FILE, RPM_VERSION_REGEX, rpm_version)
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

  GIT_HASH_REGEX = var_regex('__git_hash__')
  RPM_VERSION_REGEX = var_regex('__rpm_version__')

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

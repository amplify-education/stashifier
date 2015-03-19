module WGR
  WGRELEASE_KEY_PATH = "/home/jenkins/.ssh/wgrelease"
  SSH_PATH = "/usr/bin/ssh"
  PSSH_PATH = "/usr/bin/pssh"
  PSSH_HOST_LIST_PATH = "/opt/wgen/wgr/etc/host_list"

  # Converts the given environment name to snake_case
  # e.g. futureqa -> future_qa
  def self.env_to_snake_case(environment)
    environment.sub(/^(.+)(ci|qa)$/, '\1_\2')
  end

  #
  # Returns the autorelease host for the given environment
  #
  def self.autorelease_host(environment)
    #
    # If the env var AUTORELEASE_HOST is set, we'll assume it is directly setting
    # the host to use.
    #
    # Otherwise, if an env var like FUTURE_QA_AUTORELEASE_HOST is set for the
    # given environment, we'll use that.
    #
    # Otherwise, we use the CMDB service to look up the hostname for mhcauto
    # in the given environment.
    autorelease_host_env_var = env_to_snake_case(environment).upcase + '_AUTORELEASE_HOST'
    ENV['AUTORELEASE_HOST'] or
    ENV[autorelease_host_env_var] or
    CMDB.hosts('mhcauto', environment)[0]
  end

  #
  # Execute a command on the autorelease box for the given environment
  #
  def self.wgrelease_command(environment, args)
    host = autorelease_host(environment)
    ssh_cmd = [SSH_PATH, "-i", WGRELEASE_KEY_PATH, "wgrelease@#{host}"]
    cmd = ssh_cmd + args
    puts "Executing command: #{cmd}"
    IO.popen(cmd)
  end



  #
  # Execute a command on the given hostclass and environment
  #
  def self.hostclass_command(hostclass, environment, args)
    host_selector = "\"#{environment} #{hostclass}\""
    pssh_args = [PSSH_PATH, "--inline", "--timeout", "0", "--hosts", PSSH_HOST_LIST_PATH,
                 "-s", host_selector]
    cmd = pssh_args + args
    wgrelease_command(environment, cmd)
  end

  #
  # Perform an autorelease for the given hostclass and environment
  #
  # If supplied, use the given release version and refspec.
  # Otherwise, assume the appropriate release version for the
  # environment.
  #
  def self.autorelease(hostclass, environment, release_version=nil, refspec=nil)
    if release_version.nil? or release_version.empty? then
      if environment.match(/(current)/i)
        environment_name = $1.upcase
        release_env_var = "#{environment_name}_MCLASS_VERSION"
        require_env(release_env_var, "If the release_version is not specified, WGR.autorelease requires #{release_env_var} to be set")
        release_version = ENV[release_env_var]
      elsif environment.match(/(future)/i)
        release_version = 'mcfuture'
      else
        raise "If no release_version is specified, I can't guess one for the environment '#{environment}'."
      end
    end
    if !refspec.nil? and !refspec.empty? then
      refspec_cmd = ["--refspec", refspec]
    else
      refspec_cmd = []
    end
    wgr_cmd = ["/opt/wgen/wgr/bin/wgr.py", "-r", release_version, "-e", environment, "-f", "-s", "-g", hostclass] + refspec_cmd
    wgrelease_command(environment, wgr_cmd)
  end
end

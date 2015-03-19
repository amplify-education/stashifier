module Pip
  def self.install(opts)
    # make sure our pip is recent enough to return 0 on empty .pip files.
    sh "pip install 'pip>=1.1'" do |ok, status|
      error("pip failed") unless ok
    end
    # actually run the command
    sh "pip install --find-links #{Project[:PYNEST_URL]} #{opts}" do |ok, status|
      error("pip failed") unless ok
    end
  end
end

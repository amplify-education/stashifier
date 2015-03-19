module CMDB
  #
  # Returns the (possibly empty) list of hostnames for the given
  # hostclass and environment
  #
  def self.hosts(hostclass, environment)
    command = <<-EOS
 curl --silent 'http://cmdb.wgenhq.net/hostclass/#{hostclass}' \
 | grep -A 1 '/environment/#{environment}' \
 | perl -ne '{if (m#/hostitem/([^"]+)"#) {print "$1 ";}}'
    EOS
    hosts=`#{command}`.split
    hosts
  end
end

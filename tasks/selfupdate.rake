module Selfupdate
  TEMPLATE_PROJECT_URL = "git@github.wgenhq.net:Disco/disco_eggs_template"
  TEMPLATE_PROJECT_BRANCH = "master"
  TEMPLATE_BASE_PATH = "disco_eggs_template/templates/amplify_egg"
  TEMPLATE_UPDATE_GLOB = "rakefile tasks/*.rake tasks/*.rb tasks/lint/*rc tasks/lint/*.py jenkins/*.sh"
end

namespace "selfupdate" do
  desc "Pull down new rake task definitions from Github"
  task :pull do
    warn("Selfupdate will overwrite custom rake tasks and jenkins scripts")
    if confirm "Shall I continue the update?" then
      tempdir = `mktemp -d /tmp/rake-selfupdate-XXXXXX`.strip
      projdir = Dir.pwd
      sh "git clone #{Selfupdate::TEMPLATE_PROJECT_URL} #{tempdir}"
      sh <<-EOS
      set -e
      cd #{tempdir}
      git checkout #{Selfupdate::TEMPLATE_PROJECT_BRANCH}
      cd #{Selfupdate::TEMPLATE_BASE_PATH}
      # Update rakefile and tasks/*
      for f in #{Selfupdate::TEMPLATE_UPDATE_GLOB}
      do
        echo "Updating file: $f"
        cp "$f" "#{projdir}/$f"
      done
      # Update requirements
      for REQ in requirements.pip test-requirements.pip
      do
        # sed here captures everything on each line up to > or = or <
        # This won't parse a pip with a package index option, if you need
        # to support those please update selfupdate.rake first.
        PKGS=`cat $REQ | sed 's/\(\\\<\|\=\|\\\>\)\{1\}.*//'`
        for PKG in $PKGS
        do
          if ! grep -o $PKG "#{projdir}/$REQ" > /dev/null ; then
             echo `grep $PKG $REQ` >> "#{projdir}/$REQ"
          fi
        done
      done
      cd #{projdir}
      rm -rf "#{tempdir}"
      EOS

      notice("Rake tasks updated.")
      puts "Use 'git status' to see what has changed."
    end
  end

  desc "Perform cleanup after a selfupdate"
  task :cleanup do
    # Placeholder for migrations
    notice("Cleanup is not currently implemented")
  end
end

desc "Update the rake task definitions from Github"
task :selfupdate => ["selfupdate:pull"]


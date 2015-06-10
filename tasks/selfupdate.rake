module Selfupdate
  TEMPLATE_PROJECT_URL = "ssh://git@git.amplify.com/disco/disco_eggs_template"
  TEMPLATE_PROJECT_BRANCH = "master"
  TEMPLATE_BASE_PATH = "disco_eggs_template/templates/amplify_egg"
end

namespace "selfupdate" do
  desc "Pull down new and updated rake task definitions from the template repository"
  task :pull do
    warn("Selfupdate will overwrite custom rake tasks and jenkins scripts")
    if confirm "Shall I continue the update?" then
      tempdir = `mktemp -d /tmp/rake-selfupdate-XXXXXX`.strip
      projdir = Dir.pwd
      sh "git archive --remote=#{Selfupdate::TEMPLATE_PROJECT_URL} #{Selfupdate::TEMPLATE_PROJECT_BRANCH} #{Selfupdate::TEMPLATE_BASE_PATH} | tar -C #{tempdir} -xf -"
      sh <<-EOS
      set -e
      echo "Syncing tasks and related files from upstream..."
      rsync -rvt #{tempdir}/#{Selfupdate::TEMPLATE_BASE_PATH}/{rakefile,tasks} .
      rsync -rvt #{tempdir}/#{Selfupdate::TEMPLATE_BASE_PATH}/jenkins/*.sh jenkins
      echo Done.

      cd #{tempdir}
      cd #{Selfupdate::TEMPLATE_BASE_PATH}
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
      puts "PLEASE NOTE: if 'selfupdate.rake' has changed, you should run this task again!"
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


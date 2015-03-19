# convert wg_rpmbuild's template values to regular rpm template values
# _topdir defines the root of the rpm staging area. the value is passed automatically by wg_rpmbuild
%define _topdir $_topdir
%define checkoutroot $checkoutroot
%define version $version
%define build_number $build_number

Summary: Stash client library for Amplify utilities.
Name: stash_client
Version: %{version}
Release: %{build_number}
License: EULA
Group: MClass
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: wgen-python27
BuildRequires: wgen-python27-setuptools
BuildRequires: wgen-python27-virtualenv

Requires: wgen-python27

%description


%prep
mkdir -p %{buildroot}/opt/wgen/stash_client
# Annoyingly, the RPM workspace is right on top
# of the project checkout. We want to copy everything
# that isn't one of the RPM directories into the BUILD dir.
shopt -s extglob
cp -r %{checkoutroot}/stash_client/!(BUILD|BUILDROOT|RPMS|SOURCES|SPEC|SPRMS) .

%build
# remove the virtual env prior to building to ensure proper updates
rm -rf build_venv
/opt/wgen-3p/python27/bin/virtualenv --no-site-packages build_venv
source build_venv/bin/activate
# inject_rpm needs the dependencies installed first, so do a setup:install_deps
rake setup:install_deps
rake version:inject_git
env RPM_BUILD=%{build_number} rake version:inject_rpm
env CFLAGS="$RPM_OPT_FLAGS" rake setup:install
deactivate
/opt/wgen-3p/python27/bin/virtualenv --relocatable build_venv

%install
cp -r build_venv/* %{buildroot}/opt/wgen/stash_client
find %{buildroot}/opt/wgen/stash_client/bin -type f | xargs sed -i'' -e '1s|^#!/usr/bin/env python2.7|#!/opt/wgen/stash_client/bin/python|'

#Generate a file list for packaging
find %{buildroot}/opt/wgen/stash_client/* -type d | sed -e 's#^%{buildroot}#%dir "#' -e 's#$#"#' > INSTALLED_FILES
find %{buildroot}/opt/wgen/stash_client/* -not -type d | sed -e 's#^%{buildroot}#"#' -e 's#$#"#' >> INSTALLED_FILES

%files -f INSTALLED_FILES
%defattr(-,root,root)

%clean
rm -Rf %{buildroot}

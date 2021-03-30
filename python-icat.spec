%global python2_pkgversion 2
%if 0%{?suse_version}
%global python3_pkgversion 3
%global python3_other_pkgversion 0
%if 0%{?suse_version} < 1500
%global __python3 /usr/bin/python3
%global python2_sitelib %{python_sitelib}
%endif
%endif
%if 0%{?fedora_version}
%global python3_pkgversion 3
%global python3_other_pkgversion 0
%endif
%if 0%{?centos_version} == 600 || 0%{?rhel_version} == 600
%global python2_enable 0
%global python3_pkgversion 34
%global python3_other_pkgversion 0
%global __python2 %{__python}
%global python2_sitelib %{python_sitelib}
%global add_license 0
%else
%global python2_enable 1
%global add_license 1
%endif
%if 0%{?centos_version} == 700 || 0%{?rhel_version} == 700
%global __python3 /usr/bin/python3.6
%global __python3_other /usr/bin/python3.4
%global python3_pkgversion 36
%global python3_other_pkgversion 34
%global python3_other_sitelib /usr/lib/python3.4/site-packages
%endif

%if 0%{?centos_version} || 0%{?rhel_version} || 0%{?fedora_version}
# Turn off the brp-python-bytecompile script
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$$!!g')
%endif


Name:		python-icat
Version:	$version
Release:	1
Summary:	$description
License:	Apache-2.0
Group:		Development/Languages/Python
Url:		$url
Source:		%{name}-%{version}.tar.gz
BuildArch:	noarch
%if 0%{?python2_enable}
BuildRequires:	python%{python2_pkgversion}-devel >= 2.7
%endif
BuildRequires:	python%{python3_pkgversion}-devel >= 3.3
%if 0%{?python3_other_pkgversion}
BuildRequires:	python%{python3_other_pkgversion}-devel >= 3.3
%endif
%if 0%{?suse_version}
BuildRequires:	fdupes
%endif
BuildRoot:	%{_tmppath}/%{name}-%{version}-build

%description
$long_description


%package examples
Summary:	Python interface to ICAT and IDS
Group:		Documentation/Other
Requires:	%{name} = %{version}

%description examples
$long_description

This package contains example scripts.


%package man
Summary:	Python interface to ICAT and IDS
Group:		Documentation/Other
Requires:	%{name} = %{version}
Requires:	man

%description man
$long_description

This package contains the manual pages for the command line scripts.


%if 0%{?python2_enable}
%package -n python%{python2_pkgversion}-icat
Summary:	Python interface to ICAT and IDS
%if 0%{?centos_version} == 600 || 0%{?rhel_version} == 600
Requires:	python-argparse
%endif
Requires:	%{name} = %{version}
Requires:	python%{python2_pkgversion}-suds
%if 0%{?suse_version}
Recommends:	%{name}-man
Recommends:	python%{python2_pkgversion}-PyYAML
Recommends:	python%{python2_pkgversion}-lxml
%endif
%if 0%{?centos_version} || 0%{?rhel_version} || 0%{?fedora_version}
Requires(pre):	chkconfig
%else
Requires(pre):	update-alternatives
%endif

%description -n python%{python2_pkgversion}-icat
$long_description
%endif


%package -n python%{python3_pkgversion}-icat
Summary:	Python interface to ICAT and IDS
Requires:	%{name} = %{version}
Requires:	python%{python3_pkgversion}-suds
%if 0%{?suse_version}
Recommends:	%{name}-man
Recommends:	python%{python3_pkgversion}-PyYAML
Recommends:	python%{python3_pkgversion}-lxml
%endif
%if 0%{?centos_version} || 0%{?rhel_version} || 0%{?fedora_version}
Requires(pre):	chkconfig
%else
Requires(pre):	update-alternatives
%endif

%description -n python%{python3_pkgversion}-icat
$long_description


%if 0%{?python3_other_pkgversion}
%package -n python%{python3_other_pkgversion}-icat
Summary:	Python interface to ICAT and IDS
Requires:	%{name} = %{version}
Requires:	python%{python3_other_pkgversion}-suds
%if 0%{?centos_version} || 0%{?rhel_version} || 0%{?fedora_version}
Requires(pre):	chkconfig
%else
Requires(pre):	update-alternatives
%endif

%description -n python%{python3_other_pkgversion}-icat
$long_description
%endif


%prep
%setup -q -n %{name}-%{version}


%install
# Python 3
rm -rf build
%{__python3} setup.py install --optimize=1 --root=%{buildroot}
for f in icatdump.py icatingest.py wipeicat.py
do
    mv %{buildroot}%{_bindir}/$$f %{buildroot}%{_bindir}/$$f-%{python3_version}
done

%if 0%{?python3_other_pkgversion}
# Python 3 other
rm -rf build
%{__python3_other} setup.py install --optimize=1 --root=%{buildroot}
for f in icatdump.py icatingest.py wipeicat.py
do
    mv %{buildroot}%{_bindir}/$$f %{buildroot}%{_bindir}/$$f-%{python3_other_version}
done
%endif

%if 0%{?python2_enable}
# Python 2
rm -rf build
%{__python2} setup.py install --optimize=1 --root=%{buildroot}
for f in icatdump.py icatingest.py wipeicat.py
do
    mv %{buildroot}%{_bindir}/$$f %{buildroot}%{_bindir}/$$f-%{python2_version}
done
%endif

%__install -d -m 755 %{buildroot}%{_mandir}/man1
%__cp -p doc/man/*.1 %{buildroot}%{_mandir}/man1

%__install -d -m 755 %{buildroot}%{_docdir}/%{name}
%__cp -pr README.rst CHANGES.rst doc/* %{buildroot}%{_docdir}/%{name}
%__chmod -f a-x %{buildroot}%{_docdir}/%{name}/examples/*.py

%if 0%{?suse_version}
%fdupes %{buildroot}
%endif


%if 0%{?python2_enable}
%post -n python%{python2_pkgversion}-icat
/usr/sbin/update-alternatives --install \
    %{_bindir}/icatdump             icatdump \
        %{_bindir}/icatdump.py-%{python2_version} 20 \
    --slave %{_bindir}/icatingest   icatingest \
        %{_bindir}/icatingest.py-%{python2_version} \
    --slave %{_bindir}/wipeicat     wipeicat \
        %{_bindir}/wipeicat.py-%{python2_version}

%preun -n python%{python2_pkgversion}-icat
if [ "$$1" = 0 ] ; then
    /usr/sbin/update-alternatives --remove \
        icatdump   %{_bindir}/icatdump.py-%{python2_version}
fi
%endif


%post -n python%{python3_pkgversion}-icat
/usr/sbin/update-alternatives --install \
    %{_bindir}/icatdump             icatdump \
        %{_bindir}/icatdump.py-%{python3_version} 35 \
    --slave %{_bindir}/icatingest   icatingest \
        %{_bindir}/icatingest.py-%{python3_version} \
    --slave %{_bindir}/wipeicat     wipeicat \
        %{_bindir}/wipeicat.py-%{python3_version}

%preun -n python%{python3_pkgversion}-icat
if [ "$$1" = 0 ] ; then
    /usr/sbin/update-alternatives --remove \
        icatdump   %{_bindir}/icatdump.py-%{python3_version}
fi


%if 0%{?python3_other_pkgversion}
%post -n python%{python3_other_pkgversion}-icat
/usr/sbin/update-alternatives --install \
    %{_bindir}/icatdump             icatdump \
        %{_bindir}/icatdump.py-%{python3_other_version} 30 \
    --slave %{_bindir}/icatingest   icatingest \
        %{_bindir}/icatingest.py-%{python3_other_version} \
    --slave %{_bindir}/wipeicat     wipeicat \
        %{_bindir}/wipeicat.py-%{python3_other_version}

%preun -n python%{python3_other_pkgversion}-icat
if [ "$$1" = 0 ] ; then
    /usr/sbin/update-alternatives --remove \
        icatdump   %{_bindir}/icatdump.py-%{python3_other_version}
fi
%endif


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root)
%if 0%{?add_license}
%license LICENSE.txt
%endif
%doc %{_docdir}/%{name}
%exclude %{_docdir}/%{name}/examples
%exclude %{_docdir}/%{name}/man
%exclude %{_docdir}/%{name}/tutorial

%files examples
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/examples
%doc %{_docdir}/%{name}/tutorial

%files man
%defattr(-,root,root)
%{_mandir}/man1/*

%if 0%{?python2_enable}
%files -n python%{python2_pkgversion}-icat
%defattr(-,root,root)
%{python2_sitelib}/*
%{_bindir}/*.py-%{python2_version}
%endif

%files -n python%{python3_pkgversion}-icat
%defattr(-,root,root)
%{python3_sitelib}/*
%{_bindir}/*.py-%{python3_version}

%if 0%{?python3_other_pkgversion}
%files -n python%{python3_other_pkgversion}-icat
%defattr(-,root,root)
%{python3_other_sitelib}/*
%{_bindir}/*.py-%{python3_other_version}
%endif


%changelog

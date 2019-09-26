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
%global python3_pkgversion 34
%global python3_other_pkgversion 0
%global __python2 %{__python}
%global python2_sitelib %{python_sitelib}
%endif
%if 0%{?centos_version} == 700 || 0%{?rhel_version} == 700
%global python3_pkgversion 36
%global python3_other_pkgversion 34
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
BuildRequires:	python%{python2_pkgversion}-devel >= 2.6
BuildRequires:	python%{python3_pkgversion}-devel
%if 0%{?python3_other_pkgversion}
BuildRequires:	python%{python3_other_pkgversion}-devel
%endif
%if 0%{?suse_version}
BuildRequires:	fdupes
%endif
BuildRoot:	%{_tmppath}/%{name}-%{version}-build

%description
$long_description


%package doc
Summary:	Python interface to ICAT and IDS
Group:		Documentation/Other
Requires:	%{name} = %{version}

%description doc
$long_description

This package contains the documentation.


%package examples
Summary:	Python interface to ICAT and IDS
Group:		Documentation/Other
Requires:	%{name} = %{version}

%description examples
$long_description

This package contains example scripts.


%package -n python%{python2_pkgversion}-icat
Summary:	Python interface to ICAT and IDS
%if 0%{?centos_version} == 600 || 0%{?rhel_version} == 600
Requires:	python-argparse
%endif
Requires:	%{name} = %{version}
Requires:	python%{python2_pkgversion}-suds
%if 0%{?suse_version}
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


%package -n python%{python3_pkgversion}-icat
Summary:	Python interface to ICAT and IDS
Requires:	%{name} = %{version}
Requires:	python%{python3_pkgversion}-suds
%if 0%{?suse_version}
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

# Python 2
# Do Python 2 last because it may need patching the sources
rm -rf build
if [ %{python2_version} '<' '2.7' ]; then
    patch -p1 < python2_6.patch
fi
%{__python2} setup.py install --optimize=1 --root=%{buildroot}
for f in icatdump.py icatingest.py wipeicat.py
do
    mv %{buildroot}%{_bindir}/$$f %{buildroot}%{_bindir}/$$f-%{python2_version}
done

%__install -d -m 755 %{buildroot}%{_docdir}/%{name}
%__cp -pr README.rst CHANGES doc/* %{buildroot}%{_docdir}/%{name}
%__chmod -f a-x %{buildroot}%{_docdir}/%{name}/examples/*.py

%if 0%{?suse_version}
%fdupes %{buildroot}
%endif


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
%doc %{_docdir}/%{name}
%exclude %{_docdir}/%{name}/html
%exclude %{_docdir}/%{name}/examples

%files doc
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/html

%files examples
%defattr(-,root,root)
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/examples

%files -n python%{python2_pkgversion}-icat
%defattr(-,root,root)
%{python2_sitelib}/*
%{_bindir}/*.py-%{python2_version}

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

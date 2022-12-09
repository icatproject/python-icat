Name:		python-icat
Version:	$version
Release:	0
Url:		$url
Summary:	$description
License:	Apache-2.0
Group:		Development/Libraries/Python
Source:		%{name}-%{version}.tar.gz
BuildRequires:	python3-base >= 3.4
BuildRequires:	python3-setuptools
BuildArch:	noarch
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


%package -n python3-icat
Summary:	Python interface to ICAT and IDS
Requires:	%{name} = %{version}
Requires:	python3-packaging
Requires:	python3-suds
Recommends:	%{name}-man
Recommends:	python3-PyYAML
Recommends:	python3-lxml

%description -n python3-icat
$long_description


%prep
%setup -q -n %{name}-%{version}


%build
python3 setup.py build


%install
python3 setup.py install --optimize=1 --prefix=%{_prefix} --root=%{buildroot}
for f in `ls %{buildroot}%{_bindir}`
do
    mv %{buildroot}%{_bindir}/$$f %{buildroot}%{_bindir}/$${f%%.py}
done

%__install -d -m 755 %{buildroot}%{_mandir}/man1
%__cp -p doc/man/*.1 %{buildroot}%{_mandir}/man1

%__install -d -m 755 %{buildroot}%{_docdir}/%{name}
%__cp -pr README.rst CHANGES.rst doc/* %{buildroot}%{_docdir}/%{name}
%__chmod -f a-x %{buildroot}%{_docdir}/%{name}/examples/*.py


%files
%defattr(-,root,root)
%license LICENSE.txt
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

%files -n python3-icat
%defattr(-,root,root)
%{python3_sitelib}/*
%{_bindir}/*


%changelog

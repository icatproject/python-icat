%if 0%{?sle_version} >= 150500
%global pyversfx 311
%global python %__python311
%global python_sitelib %python311_sitelib
%else
%global pyversfx 3
%global python %__python3
%global python_sitelib %python3_sitelib
%endif

Name:		python-icat
Version:	$version
Release:	0
Url:		$url
Summary:	$description
License:	Apache-2.0
Group:		Development/Libraries/Python
Source:		https://github.com/icatproject/python-icat/releases/download/%{version}/python-icat-%{version}.tar.gz
BuildRequires:	python%{pyversfx}-base >= 3.4
BuildRequires:	python%{pyversfx}-setuptools
BuildRequires:	fdupes
BuildRequires:	python-rpm-macros
BuildArch:	noarch

%description
$long_description


%package examples
Summary:	$description
Group:		Documentation/Other
Requires:	%{name} = %{version}

%description examples
$long_description

This package contains example scripts.


%package man
Summary:	$description
Group:		Documentation/Other
Requires:	%{name} = %{version}
Requires:	man

%description man
$long_description

This package contains the manual pages for the command line scripts.


%package -n python%{pyversfx}-icat
Summary:	$description
Requires:	%{name} = %{version}
Requires:	python%{pyversfx}-lxml
Requires:	python%{pyversfx}-packaging
Requires:	python%{pyversfx}-suds
Recommends:	%{name}-man
Recommends:	python%{pyversfx}-PyYAML

%description -n python%{pyversfx}-icat
$long_description


%prep
%setup -q -n %{name}-%{version}


%build
%{python} setup.py build


%install
%{python} setup.py install --optimize=1 --prefix=%{_prefix} --root=%{buildroot}
for f in `ls %{buildroot}%{_bindir}`
do
    mv %{buildroot}%{_bindir}/$$f %{buildroot}%{_bindir}/$${f%%.py}
done
%__install -d -m 755 %{buildroot}%{_datadir}/icat
%__cp -p etc/ingest-*.xsd etc/ingest.xslt %{buildroot}%{_datadir}/icat
%__install -d -m 755 %{buildroot}%{_mandir}/man1
%__cp -p doc/man/*.1 %{buildroot}%{_mandir}/man1
%__install -d -m 755 %{buildroot}%{_docdir}/%{name}
%__cp -pr README.rst CHANGES.rst doc/* %{buildroot}%{_docdir}/%{name}
%__chmod -f a-x %{buildroot}%{_docdir}/%{name}/examples/*.py
%fdupes %{buildroot}%{python_sitelib}


%files
%defattr(-,root,root)
%license LICENSE.txt
%{_datadir}/icat
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

%files -n python%{pyversfx}-icat
%defattr(-,root,root)
%{python_sitelib}/*
%{_bindir}/*


%changelog

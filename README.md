# aleph-holdings
Retrieve holdings for Aleph records from Voyager-databases.

## holdings_proxy.cgi

Get holdings information for a record to be used in a webpage

### URL parameters:

**id**: ID of the record

**lib**: ID of the library where the holdings information is to fetched from

**callback**: A JSONP callback

Example configuration is provided in _res/holdings_proxy_example.config_.

## holdings.cgi

Get redirection link to a record's holdings information in a library's OPAC.

### URL parameters:

**id**: ID of the record

**lib**: ID of the library where the holdings information is to fetched from

Example configuration is provided in _res/holdings_example.config_.

## holdings.js ##

Replaces links to holdings information with the actual information with also retaining the links.

## Dependencies

### Perl

CGI

Cwd

LWP::UserAgent

HTTP::Request

File::Basename

XML::DOM

### Javascript

[jQuery 1.3.2](https://github.com/jquery/jquery)

[jquery.cookie](https://github.com/carhartl/jquery-cookie)

## Licensing

Copyright (c) 2015 University Of Helsinki (The National Library Of Finland)

Licensed under GNU Affero GPL version 3.

### Licenses of dependencies

All the dependencies are free software.

#### Licenses of the packaged dependencies ####

**jquery**: MIT or GPL license

**jquery.cookie**: MIT-license
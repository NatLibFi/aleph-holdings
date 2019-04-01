#!/opt/CSCperl/current/bin/perl 
#
# Aleph Central Catalog -> Voyager holdings redirector
# Copyright (c) 2015-2017 University Of Helsinki (The National Library Of Finland)
#  
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#  
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Aleph Central Catalog -> Voyager holdings redirector
# v1.1 for Aleph 18
# 2008 Ere Maijala / The National Library of Finland

# Required parameters when called via cgi:
# id   the 001 of the source record
# lib  Aleph owning library ID

use strict;
use CGI qw(:standard);
use LWP::UserAgent;
use HTTP::Request::Common;
use Cwd 'abs_path';
use File::Basename qw(dirname);

my $cmd_path = dirname(abs_path($0));
my $config_ref = do("$cmd_path/holdings.config");
die("Could not parse configuration: $@") if ($@ || !$config_ref);
my %config = %$config_ref;

# MAIN
{
  my $id = param('id');
  my $lib = param('lib');

  if (!$id || !$lib)
  {
    fail('Mandatory parameter missing');
  }

  if (!defined($config{'libraries'}{$lib}))
  {
    fail('Unknown lib');
  }

  my $fieldlist = get_record($id);

  my $original_id = '';
  foreach my $field (@$fieldlist)
  {
    if ($field->{'code'} eq 'SID')
    {
      debugout("Checking SID field $field->{'data'}");
      my $sid_b = get_subfield($field->{'data'}, 'b');
      if (lc($sid_b) eq lc($lib))
      {
        my $sid_c = get_subfield($field->{'data'}, 'c');
        debugout("Found original ID $sid_c");
        $original_id = $sid_c;
        last;
      }
    }
  }

   my @kids = ();   # Melinda-ID's & 035
     
   foreach my $field (@$fieldlist)
    { 
      # get from field Melinda,  001
      if ($field->{'code'} eq '001') 
      {
		    my $f001=$field->{'data'};
		    $f001 =~ s/\x1e//g;  
        push(@kids, $f001);
        debugout("f001=".$field->{'data'}."edited to ".$f001);
      } 

      # get from field 035 subfields $a and $z
      # get from field 035 subfields $a and $z
      if ($field->{'code'} eq '035')
      {
        my $f035a = get_subfield($field->{'data'}, 'a');
        my $f035z = get_subfield($field->{'data'}, 'z');

		    if ($f035a =~ m/\(FI-MELINDA\)/)
        {
			    $f035a =~ s/\(FI-MELINDA\)//g ;	
			    push(@kids,$f035a);
			    debugout("f035a=".$f035a." pushed to list.");	
		    }

		    if ($f035z =~ m/\(FI-MELINDA\)/)
        {
			    $f035z =~ s/\(FI-MELINDA\)//g ;
			    push(@kids,$f035z);
			    debugout("f035z=".$f035z." pushed to list.");	
		    }
      
      }

	}

  if ($original_id =~ /^FCC(\d+)/)
  {
    $id = $1;
	push(@kids,$1);
    $original_id = '';
  }


  my $url = $config{'libraries'}{$lib}{'url'};
  my $opacType = $config{'libraries'}{$lib}{'type'} || 'default';

  if ($url !~ /[\?&]$/)
  {
    if ($url =~ /\?/)
    {
      $url .= '&';
    }
    else
    {
      $url .= '?';
    }
  }

   $url .= 'gid=' . url_encode($id);
  
  foreach my $kid (@kids) {
	  $url .= '&gid=' . url_encode($kid);
  }

  if ($original_id) {
	  $url .= '&lid=' . url_encode($original_id);
  }

  if (defined($config{'libraries'}{$lib}{'ils'}) && $config{'libraries'}{$lib}{'ils'} == 'koha')
  {
    # All Koha-libraries should have finna-opac
    if ($original_id ne '') {
      $url = $config{'libraries'}{$lib}{'finna_url'} . url_encode($original_id);
    }  
    else {
      $url = $config{'libraries'}{$lib}{'finna_url'};
      $url =~ s/Record.*//;
    }
  }

  else {
    if ($opacType eq 'finna') {
    #	if ($original_id eq '') {
      $original_id = get_bibid_from_local($url);
    #	}
	  unless ($original_id) {
		  fail('No original ID found.');
	  }
    $url = $config{'libraries'}{$lib}{'finna_url'} . url_encode($original_id);
    }
  }

  debugout("Redirecting to $url");

  print redirect($url);
}

sub uniq {
	my %seen;
	return grep { !$seen{$_}++ } @_;
}

sub get_bibid_from_local($) {

  my $url = shift;

  my $ua = new LWP::UserAgent;
  $ua->max_redirect(0);

  do {
    my $response = $ua->get($url);
    $url = $response->header('Location');

    my ($bibId) = $url =~ /.*bibId=(.*)$/;  # Tomcat
	my ($bibId2) = $url =~ /.*BBID=(.*)$/;  # Classic

    if (defined($bibId)) {
		return $bibId;    
    }
	if (defined($bibId2)) {
		return $bibId2;
	}

  } while (defined($url));

  return undef;
}

sub get_record($)
{
  my ($a_id) = @_;

  my $x_request = "$config{'aleph_x_server'}op=find-doc&doc_num=$a_id&base=$config{'aleph_library'}";

  my $ua = LWP::UserAgent->new(timeout => 60, agent => 'Mozilla/4.0 (compatible; Aleph Replication Client;)');
  my $request = HTTP::Request->new(GET => $x_request);
  my $response = $ua->request($request);
  if (!$response->is_success())
  {
    error("X-Server request $x_request failed: " . $response->code . ': ' . $response->message . ', content: ' . $response->content);
    return undef;
  }

  my $xml = $response->content;
  if ($xml =~ /<error>(.*)<\/error>/)
  {
    error("X-Server request $x_request returned error: $1");
    return undef;
  }

  debugout("X-Server response: $xml");

  my @list = ();
  my $field_start = "\x1f";
  my $field_end = "\x1e";

  my ($data) = $xml =~ /<oai_marc>(.*?)<\/oai_marc>/s;

  while ($data =~ s/<fixfield(.*?)>(.*?)<\/fixfield>//s)
  {
    my $attrs = $1;
    my $contents = xml_decode($2);
    my ($tag) = $attrs =~ /id="(.*?)"/;

    next if ($tag eq 'FMT');
    if ($tag eq 'LDR')
    {
      $tag = '000';
      $contents = justifyleftch($contents, 24, '0');
    }
    $contents =~ s/\^/ /g;
    $contents .= $field_end;
    push(@list, {'code' => $tag, 'data' => $contents});
  }

  while ($data =~ s/<varfield(.*?)>(.*?)<\/varfield>//s)
  {
    my $attrs = $1;
    my $contents = $2;
    my ($tag) = $attrs =~ /id="(.*?)"/;
    my ($ind1) = $attrs =~ /i1="(.*?)"/;
    my ($ind2) = $attrs =~ /i2="(.*?)"/;

    my $fielddata = justifyleftch($ind1, 1, ' ') . justifyleftch($ind2, 1, ' ');
    while ($contents =~ s/<subfield([\x00-\xFF]*?)>([\x00-\xFF]*?)<\/subfield>//)
    {
      my $sub_attrs = $1;
      my $sub_contents = xml_decode($2);
      my ($sub_code) = $sub_attrs =~ /label="(.*?)"/;

      $sub_contents =~ s/\r\n/ /g;
      $sub_contents =~ s/\r//g;
      $sub_contents =~ s/\n/ /g;

      $fielddata .= "$field_start$sub_code$sub_contents";
    }
    $fielddata .= $field_end;

    push(@list, {'code' => $tag, 'data' => $fielddata});
  }

  return \@list;
}

sub fail($)
{
  my ($msg) = @_;

  print header(-type => 'text/html', -charset => 'UTF-8', -expires => 'Thu, 25-Apr-1999 00:40:33 GMT');
  print "<html><head><title>Error</title></head><body><h1>$msg</h1></body></html>\n";
  exit;
}

sub url_encode($)
{
  my ($str) = @_;

  $str =~ s/([^A-Za-z0-9\-])/sprintf("%%%02X", ord($1))/seg;
  $str =~ s/%20/\+/g;
  return $str;
}

sub error($)
{
  my ($str) = @_;

  print STDERR "$str\n";
}

sub debugout($)
{
  my ($str) = @_;

  return if (!$config{'debug'});

  print STDERR "$str\n";
}

sub justifyleftch($$$)
{
  my ($str, $len, $padch) = @_;

  $str = substr($str, 0, $len);
  while (length($str) < $len)
  {
      $str = $str . $padch;
  }
  return $str;
}

sub xml_decode($)
{
  my ($str) = @_;

  $str =~ s/&amp;/&/g;
  $str =~ s/&lt;/</g;
  $str =~ s/&gt;/>/g;

  return $str;
}

sub get_subfield($$)
{
  my ($a_fielddata, $a_subfield) = @_;

  my ($subfield) = $a_fielddata =~ /\x1f$a_subfield(.*?)[\x1e\x1f]/;
  return $subfield;
}

sub get_field($$)
{
  my ($a_list, $a_field) = @_;

  my $fields = scalar(@$a_list);
  for (my $i = 0; $i < $fields; $i++)
  {
    my $code = $a_list->[$i]{'code'};
    if ($code eq $a_field)
    {
      return $a_list->[$i]{'data'};
    }
  }
  return '';
}

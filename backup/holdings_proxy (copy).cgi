#!/opt/CSCperl/current/bin/perl
#!/usr/bin/perl
#
# Voyager XML holdings proxy -> JSON
# Copyright (c) 2015 University Of Helsinki (The National Library Of Finland)
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
# v1.1 for Aleph 18
# 2008 Ere Maijala / The National Library of Finland
#
# Required parameters when called via cgi:
# id   the 001 of the source record
# lib  Aleph owning library ID  / v.2017.12.1

use strict;
use CGI qw(:standard);
use LWP::UserAgent;
use HTTP::Request::Common;
use XML::DOM;
use Cwd 'abs_path';
use File::Basename qw(dirname);

my $cmd_path = dirname(abs_path($0));
my $config_ref = do("$cmd_path/holdings_proxy_esa.config");         # HUOM. !!!
die("Could not parse configuration: $@") if ($@ || !$config_ref);
my %config = %$config_ref;

my $g_lib = '';
my $g_callback = '';

# MAIN
{
  binmode(STDOUT, ":utf8");

  my $is_aurora_ils;
  my $id = param('id');
  my $lib = param('lib');
  my $callback = param('callback');

  if (!$id || !$lib)
  {
    fail('Mandatory parameter missing');
  }

  $g_lib = $lib;
  $g_callback = $callback;

  fail('Unknown lib') if (!defined($config{'libraries'}{$lib}));

  my $fieldlist = get_record($id);

  my $original_id = '';
  my @sids = ();

  if (defined($config{'libraries'}{$lib}{'ils'}) && $config{'libraries'}{$lib}{'ils'} == 'aurora') {
    $is_aurora_ils = 1;
  }

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
        push(@sids, $sid_c);
        if (!$is_aurora_ils) {
          last;
        }
      }
    }
  }

  ##################  2017 IX ################  MELINDA-193
  my $testi = "just testing";
   my @kids = ();   # Melinda-ID's & 035
     
   foreach my $field (@$fieldlist)
    { 
      # get from field Melinda,  001
      if ($field->{'code'} eq '001') 
      {
        push(@kids, $field->{'data'});
      } 

      # get from field 035
      if ($field->{'code'} eq '035')
      {
        my $found = $field->{'data'}  ;
           $found =~ s/^....\(FI-MELINDA\)//g ;
        push(@kids, $found);
      }

      # get from DATA where there is Melinda number 
      if ($field->{'data'} =~ /^....\(FI-MELINDA\).*/ ) {             
        my $found = $field->{'data'}  ;
           $found =~ s/^....\(FI-MELINDA\)//g ; 
       push(@kids, $found); 
      }

   } # foreach my $field <-


  ################# 2017 IX  #################  <- MELINDA-193

  if ($original_id =~ /^FCC(\d+)/)
  {
    $id = $1;
    $original_id = '';
  }

  my $url = $config{'libraries'}{$lib}{'url'};
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

   push(@kids, url_encode($id) );

################# 2017 IX -B-  #################  -> MELINDA-193
# $testi .= " \n url (original): " . $url ;

            my $previous="";
            my @sortedArray = sort(@kids);
               @kids = @sortedArray;
  
  foreach my $kidsrow (@kids) {
             chop($kidsrow);

  	if ($previous eq $kidsrow) { }  # skip
           else {
	      $url = $url .  "&globalBibId=" . url_encode($kidsrow) ;
              $previous = $kidsrow;
       }
  }

$testi .= " \n url: (added_&_uniqd) " . $url ;

################# 2017 IX -B-  #################  <- MELINDA-193

  if ($is_aurora_ils) {
    foreach my $lid (@sids) {
      $url .= '&localBibId=' . url_encode($lid);
    }  
  } else {
    $url .= '&localBibId=' . url_encode($original_id);
  }
  
  debugout("url=$url");

  print header(-type => 'application/json', -charset => 'UTF-8', -expires => 'Thu, 25-Apr-1999 00:40:33 GMT',
    -pragma => 'no-cache', -Cache_Control => 'private, no-cache, no-store, must-revalidate, max-age=0, pre-check=0, post-check=0');

  my $ua = LWP::UserAgent->new(timeout => 60, agent => 'Mozilla/4.0 (compatible; Aleph Holdings Proxy;)');
  my $request = HTTP::Request->new(GET => $url);
  my $response = $ua->request($request);
  if (!$response->is_success())
  {
    fail("Holdings request $url failed: " . $response->code . ': ' . $response->message);
  }

  my $parser = new XML::DOM::Parser;
  my $doc;
  eval { $doc = $parser->parse($response->content) };
  if ($@)
  {
    fail("Could not parse holdings response: $!");
  }

  my $json = '';
  my @mfhds = $doc->getElementsByTagName('mfhd');
  foreach my $mfhd (@mfhds)
  {
    my $record = $mfhd->getElementsByTagName('record');

    my %fields = ();

    my $marcref = $record && marcxml_to_fieldlist($record->item(0));
    $fields{'location'} = '';
    my $fields = get_field_count($marcref, '852');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f852 = get_field_num($marcref, '852', $i);
      $fields{'location'} .= '<br>' if ($i > 1);
      my $f852k = get_subfield($f852, 'k');
      my $f852h = get_subfield($f852, 'h');
      my $f852i = get_subfield($f852, 'i');
      my $f852j = get_subfield($f852, 'j');
      my $f852z = get_subfield($f852, 'z');
      $fields{'location'} .= "$f852k" if ($f852k);
      $fields{'location'} .= " $f852h" if ($f852h);
      $fields{'location'} .= " $f852i" if ($f852i);
      $fields{'location'} .= " $f852j" if ($f852j);
      $fields{'location'} .= " ($f852z)" if ($f852z);
      $fields{'location'} =~ s/^\s//;
    }

    my $f856 = get_field($marcref, '856');
    $fields{'electronic_prefix'} = get_subfield($f856, '3');
    $fields{'electronic_link'} = get_subfield($f856, 'u');
    $fields{'electronic_link_text'} = get_subfield($f856, 'v');
    $fields{'electronic_link_note'} = get_subfield($f856, 'z');

    $fields = get_field_count($marcref, '506');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f506 = get_field_num($marcref, '506', $i);
      $fields{'restrictions'} .= '<br>' if ($i > 1);
      $fields{'restrictions'} .= get_subfield($f506, 'a');
    }

    $fields = get_field_count($marcref, '845');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f845 = get_field_num($marcref, '845', $i);
      $fields{'restrictions'} .= '<br>' if ($i > 1);
      $fields{'restrictions'} .= get_subfield($f845, 'a');
    }

    $fields{'holdings_stmt'} = '';
    $fields = get_field_count($marcref, '863');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f863 = get_field_num($marcref, '863', $i);
      $fields{'holdings_stmt'} .= '<br>' if ($i > 1);
      my $f863a = get_subfield($f863, 'a');
      my $f863b = get_subfield($f863, 'b');
      my $f863i = get_subfield($f863, 'i');
      my $f863g = get_subfield($f863, 'g');
      my $f863z = get_subfield($f863, 'z');
      $fields{'holdings_stmt'} .= "$f863a" if ($f863a);
      $fields{'holdings_stmt'} .= " $f863b" if ($f863b);
      $fields{'holdings_stmt'} .= " $f863i" if ($f863i);
      $fields{'holdings_stmt'} .= " $f863g" if ($f863g);
      $fields{'holdings_stmt'} .= " ($f863z)" if ($f863z);
      $fields{'holdings_stmt'} =~ s/^\s//;
    }

    $fields{'textual_holdings_stmt'} = '';
    $fields = get_field_count($marcref, '866');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f866 = get_field_num($marcref, '866', $i);
      $fields{'textual_holdings_stmt'} .= '<br>' if ($i > 1);
      my $f866a = get_subfield($f866, 'a');
      my $f866z = get_subfield($f866, 'z');
      $fields{'textual_holdings_stmt'} .= "$f866a" if ($f866a);
      $fields{'textual_holdings_stmt'} .= " ($f866z)" if ($f866z);
      $fields{'textual_holdings_stmt'} =~ s/^\s//;
    }

 ######### add IX 2017 ##########

  my @newIssues = $doc->getElementsByTagName('newIssue');     

    foreach my $issue (@newIssues) {
      my $item_enum = $issue->getAttributeNode('itemEnum')->getValue();
       $fields{'textual_holdings_stmt'} .= "<br> - "  . "$item_enum" if ($item_enum);
    }  

 ######### add IX 2017 #########

    
    $fields{'supplements'} = '';
    $fields = get_field_count($marcref, '867');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f867 = get_field_num($marcref, '867', $i);
      $fields{'supplements'} .= '<br>' if ($i > 1);
      my $f867a = get_subfield($f867, 'a');
      my $f867z = get_subfield($f867, 'z');
      $fields{'supplements'} .= "$f867a" if ($f867a);
      $fields{'supplements'} .= " -- $f867z" if ($f867z);
    }

    $fields{'indexes'} = '';
    $fields = get_field_count($marcref, '868');
    for (my $i = 1; $i <= $fields; $i++)
    {
      my $f868 = get_field_num($marcref, '868', $i);
      $fields{'indexes'} .= '<br>' if ($i > 1);
      my $f868a = get_subfield($f868, 'a');
      my $f868z = get_subfield($f868, 'z');
      $fields{'indexes'} .= "$f868a" if ($f868a);
      $fields{'indexes'} .= " -- $f868z" if ($f868z);
    }


    $fields{'item_count'} = 0;
    $fields{'items_available'} = 0;
    $fields{'first_due_date'} = '';

    my @item_locations = ();
    my %items_at_location = ();
    my %available_at_location = ();
    my %first_due_at_location = ();
    my @items = $mfhd->getElementsByTagName('item');
    foreach my $item (@items)
    {
      ++$fields{'item_count'};

      my $due_date = $item->getAttributeNode('dueDate')->getValue();
      $due_date =~ s/^(\d+\.\d+\.\d+).*/$1/;
      $fields{'first_due_date'} = $due_date if ($due_date && (!$fields{'first_due_date'} || $due_date lt $fields{'first_due_date'}));

      my $available = 1;
      my @statuses = $item->getElementsByTagName('status');
      foreach my $status (@statuses)
      {
        my $code = $status->getAttributeNode('code')->getValue();
        $available = 0 if ($code != 1 && $code != 11);
      }
      ++$fields{'items_available'} if ($available);

      my $perm_loc = $item->getAttributeNode('permLocation')->getValue();
      my $temp_loc = $item->getAttributeNode('tempLocation')->getValue();
      my $json_loc = json_escape($temp_loc ? $temp_loc : $perm_loc);
      push(@item_locations, $json_loc) unless($items_at_location{$json_loc}++);
      $available_at_location{$json_loc}++ if ($available);
      $first_due_at_location{$json_loc} = $due_date if ($due_date && (!$first_due_at_location{$json_loc} || $due_date lt $first_due_at_location{$json_loc}));
    }




    my $fields_text = '';
    foreach my $key (sort keys %fields)
    {
      my $value = $fields{$key};
      $value =~ s/<br>$//;
      $value = json_escape($value);
      $fields_text .= ",\n" if ($fields_text);
      $fields_text .= "      \"$key\": \"$value\"";
    }
    my $locations_text = '';
    foreach my $loc (@item_locations)
    {
      my $count = $items_at_location{$loc};
      my $available = $available_at_location{$loc} || 0;
      my $first_due = $first_due_at_location{$loc};
      $locations_text .= ",\n" if ($locations_text);
      $locations_text .= "        { \"location\": \"$loc\", \"items\": \"$count\", \"available\": \"$available\", \"first_due_date\": \"$first_due\" }";
    }

 ####### -> IIX & IX 2017 - ########## >
   my $text = qw/location/;  
   my $testaus = $doc->getElementsByTagName($text)->item(0);
   if (defined $testaus) {  
     
       my $perm_loc_extra = "";
      foreach my $location_extra ($doc->getElementsByTagName('mfhd')){
        $perm_loc_extra = $location_extra->getElementsByTagName('location')->item(0)->getAttribute('dispname');
      }

      if (length($locations_text) == 0)  {
      $locations_text= "      { \"location\": \"$perm_loc_extra\",}"; 
      }  
       
   }
 
####### <- IIX & IX 2017 - ######### <-

 $locations_text = $testi;           # shows the URL  

    $fields_text .= qq|,
      "item_locations": [
       $locations_text
      ]|;
    $json .= ",\n" if ($json);
    $json .= qq|    {
$fields_text
    }|;
  }
  my $lib_escaped = json_escape($lib);
  my $error = $doc->getElementsByTagName('error');
  my $error_json = $error && '  "error": "' . json_escape(get_xml_text($error->item(0))) . "\",\n";
  $json = qq|{ "holdings": {
$error_json  "lib": "$lib_escaped",
  "mfhd": [
$json
  ]
  }
}
|;
  if ($callback)
  {
    print("$callback($json);\n");
  }
  else
  {
    print("var ${lib}_holdings = $json;\n");
  }
}

sub get_record($)
{
  my ($a_id) = @_;

  my $x_request = "$config{'aleph_x_server'}op=find-doc&doc_num=$a_id&base=$config{'aleph_library'}";

  my $ua = LWP::UserAgent->new(timeout => 60, agent => 'Mozilla/4.0 (compatible; Aleph Holdings Proxy;)');
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

  print STDERR "holdingsproxy: $msg\n";

  my $lib_escaped = json_escape($g_lib);
  my $error_json = '  "error": "' . json_escape($msg) . "\",\n";
  my $json = qq|{ "holdings": {
$error_json  "lib": "$lib_escaped",
  }
}
|;
  if ($g_callback)
  {
    print("$g_callback($json);\n");
  }
  else
  {
    print("var ${g_lib}_holdings = $json;\n");
  }

  exit;
}

sub url_encode($)
{
  my ($str) = @_;

  $str =~ s/([^A-Za-z0-9\-])/sprintf("%%%02X", ord($1))/seg;
  $str =~ s/%20/\+/g;
  return $str;
}

sub json_escape($)
{
  my ($str) = @_;

  $str =~ s/\\/\\\\/g;
  $str =~ s/\"/\\\"/g;

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

  foreach my $field (@$a_list)
  {
    if ($field->{'code'} eq $a_field)
    {
      return $field->{'data'};
    }
  }
  return '';
}

sub get_field_num($$$)
{
  my ($a_list, $a_field, $a_field_num) = @_;

  my $field_num = 1;
  foreach my $field (@$a_list)
  {
    if ($field->{'code'} eq $a_field && $field_num++ == $a_field_num)
    {
      return $field->{'data'};
    }
  }
  return '';
}

sub get_field_count($$)
{
  my ($a_list, $a_field) = @_;

  my $field_count = 0;
  foreach my $field (@$a_list)
  {
    ++$field_count if ($field->{'code'} eq $a_field);
  }
  return $field_count;
}


sub get_xml_text($)
{
  my ($xmldoc) = @_;

  return '' if (!$xmldoc);

  foreach my $child ($xmldoc->getChildNodes())
  {
    my $type = $child->getNodeType();
    return $child->getNodeValue() if ($type == TEXT_NODE || $type == CDATA_SECTION_NODE);
  }
  return '';
}

sub marcxml_to_fieldlist($)
{
  my ($record) = @_;
  my $field_start = "\x1f";
  my $field_end = "\x1e";

  my @list = ();

  my $leader = get_xml_text($record->getElementsByTagName('leader')->item(0));
  $leader = justifyleftch($leader, 24, ' ');
  push(@list, {'code' => '000', 'data' => $leader});

  my @controlfields = $record->getElementsByTagName('controlfield');
  foreach my $controlfield (@controlfields)
  {
    my $tag = $controlfield->getAttributeNode('tag')->getValue();
    my $contents = get_xml_text($controlfield);

    push(@list, {'code' => $tag, 'data' => $contents});
  }

  my @datafields = $record->getElementsByTagName('datafield');
  foreach my $datafield (@datafields)
  {
    my $tag = $datafield->getAttributeNode('tag')->getValue();
    my $ind1 = $datafield->getAttributeNode('ind1')->getValue();
    my $ind2 = $datafield->getAttributeNode('ind2')->getValue();

    my $fielddata = justifyleftch($ind1, 1, ' ') . justifyleftch($ind2, 1, ' ');

    my @subfields = $datafield->getElementsByTagName('subfield');
    foreach my $subfield (@subfields)
    {
      my $sub_code = $subfield->getAttributeNode('code')->getValue();
      my $sub_contents = get_xml_text($subfield);
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

/**
*
* @licstart  The following is the entire license notice for the 
*  JavaScript code in this page.
*
* Embed record holdings (Retrieved with holdings_proxy.cgi) in HTML
* Copyright (c) 2015 University Of Helsinki (The National Library Of Finland)
*
* This file is part of aleph-holdings
*  
* aleph-holdings is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*  
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Affero General Public License for more details.
*  
* You should have received a copy of the GNU Affero General Public License
* along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
* @licend  The above is the entire license notice
* for the JavaScript code in this page.
*
*/

var ec_texts = new Array();

// Note: table id must be #recordtable

if (g_current_language == "eng")
{
  ec_texts['ec_first_heading_regexp'] = '(Subject|LCSH|MeSH|NAL|Genre|Occupation|Function|Other Keywords|UDC|Dewey|Classification)';
  ec_texts['ec_stop_at_heading_regexp'] = '(Owning Libraries|Holdings|Other libraries)';
  ec_texts['ec_first_separator'] = 'Subjects and Classifications';
  ec_texts['ec_first_separator_match'] = 'Subjects and Classifications';
  ec_texts['ec_show_button_alt'] = 'Show';
  ec_texts['ec_hide_button_alt'] = 'Hide';
  ec_texts['ec_second_separator'] = 'Owning Libraries';
}
else if (g_current_language == "swe")
{
  ec_texts['ec_first_heading_regexp'] = '(Behand|LCSH|MeSH|NAL|mnesord|Genre eller|Yrke|Funktion|Andra s|klassifikation|mneskategori)';
  ec_texts['ec_stop_at_heading_regexp'] = '(gande bibliotek|ndsuppgifter|Andra bibliotek)';
  ec_texts['ec_first_separator'] = '&Auml;mnesord och klassifikationer';
  ec_texts['ec_first_separator_match'] = 'mnesord och klassifikationer';
  ec_texts['ec_show_button_alt'] = 'Visa';
  ec_texts['ec_hide_button_alt'] = 'G&ouml;mma';
  ec_texts['ec_second_separator'] = '&Auml;gande bibliotek';
}
else
{
  ec_texts['ec_first_heading_regexp'] = '(Asiasana|Kohdehenkil|Kohdeyhteis|Kokous kohteena|Kohdeteos|asiasana|Lajityyppi|Ammatti hakutermin|Tapahtuma|Muita hakusanoja|luokitus|Aihealuekoodi|luokituksia)';
  ec_texts['ec_stop_at_heading_regexp'] = '(Saatavuustiedot|Varastotiedot|Muut kirjastot)';
  ec_texts['ec_first_separator'] = 'Asiasanat ja luokitukset';
  ec_texts['ec_first_separator_match'] = 'Asiasanat ja luokitukset';
  ec_texts['ec_show_button_alt'] = 'N&auml;yt&auml;';
  ec_texts['ec_hide_button_alt'] = 'Piilota';
  ec_texts['ec_second_separator'] = 'Saatavuustiedot';
}

$(document).ready(function()
{
  var td = find_first_td();
  if (!td)
    return;
  var tr = td.parent();

  tr.before('<tr id="first_fieldset_separator"><td class="text3" colspan="2"><u><img id="expand_fields" src="/plus.png" alt="' + ec_texts['ec_show_button_alt'] + '" onclick="expand_collapse(false)" style="display: none;"><img id="collapse_fields" src="/minus.png" alt="' + ec_texts['ec_hide_button_alt'] + '" onclick="expand_collapse(true)">&nbsp;' + ec_texts['ec_first_separator'] + '</u></td></tr>\n');

  td = find_last_td();
  if (td)
  {
    tr = td.eq(0).parent();
    tr.before('<tr id="second_fieldset_separator"><td class="text3" colspan="2"><u>' + ec_texts['ec_second_separator'] + '</u></td></tr>\n');
    tr.find("td:eq(0)").text("");
    tr.nextAll().find("td:eq(0)").text("");
  }

  if ($.cookie('collapse_descriptive_fields') == 'true')
    expand_collapse(true);
});

function find_first_td()
{
  var tds = $("table#recordtable").find("td");
  for (var i = 0; i < tds.length; i++)
  {
    var td = tds.eq(i);
    if (td.get(0).cellIndex != 0)
      continue;
    var txt = td.text();
    if (txt.match(ec_texts['ec_first_heading_regexp']) && txt.indexOf(ec_texts['ec_first_separator_match']) < 0)
    {
      return td;
    }
  }

  return null;
}

function find_last_td()
{
  var tds = $("table#recordtable").find("td");
  for (var i = 0; i < tds.length; i++)
  {
    var td = tds.eq(i);
    if (td.get(0).cellIndex != 0)
      continue;
    var txt = td.text();
    if (txt.match(ec_texts['ec_stop_at_heading_regexp']))// && txt.indexOf(ec_texts['ec_second_separator']) < 0)
    {
      return td;
    }
  }

  return null;
}

function expand_collapse(collapse)
{
  var td = find_first_td();
  if (!td)
    return;

  var tr = td.parent();
  var table = tr.parent();
  var idx_first = table.children().index(tr);

  var idx_last = idx_first;
  tr = tr.next();

  while (tr.length > 0 && idx_last < 1000)
  {
    var td = tr.find("td:first");
    if (td.get(0).cellIndex != 0)
      continue;
    var txt = td.text();
    if (txt.match(ec_texts['ec_stop_at_heading_regexp']))// && txt.indexOf(ec_texts['ec_second_separator']) < 0)
      break;

    ++idx_last;
    tr = tr.next();
  }

  if (idx_first == idx_last)
    return;

  //++idx_last;
  if (collapse)
  {
    table.find("tr").slice(idx_first, idx_last).hide();

    $("#collapse_fields").hide();
    $("#expand_fields").show();
    $.cookie('collapse_descriptive_fields', 'true', { expires: 7 });
  }
  else
  {
    table.find("tr").slice(idx_first, idx_last).show();
    $("#expand_fields").hide();
    $("#collapse_fields").show();
    $.cookie('collapse_descriptive_fields', 'false', { expires: 7 });
  }
}

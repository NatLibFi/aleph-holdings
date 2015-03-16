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

var texts = new Array();

if (g_current_language == "eng")
{
  texts['items'] = 'Items:';
  texts['available'] = 'available:';
  texts['first_due'] = 'first due date:';
  texts['location'] = 'Location';
  texts['restrictions'] = 'Restrictions';
  texts['electronic'] = 'Electronic material';
  texts['holdings'] = 'Holdings';
  texts['supplements'] = 'Supplements';
  texts['indexes'] = 'Indexes';
  texts['expand'] = 'Show';
  texts['collapse'] = 'Hide';
  texts['error'] = 'Information not available';
}
else if (g_current_language == "swe")
{
  texts['items'] = 'Exemplar:';
  texts['available'] = 'tillg&auml;ngliga:';
  texts['first_due'] = 'F&ouml;rst f&ouml;rfallodag:';
  texts['location'] = 'L&auml;ge';
  texts['restrictions'] = 'Anv&auml;ndningsbegr&auml;nsningar';
  texts['electronic'] = 'Elektroniskt material';
  texts['holdings'] = 'Best&aring;ndsuppgifter';
  texts['supplements'] = 'Supplement';
  texts['indexes'] = 'Index';
  texts['expand'] = 'Visa';
  texts['collapse'] = 'G&ouml;mma';
  texts['error'] = 'Information inte tillg&auml;nglig';
}
else
{
  texts['items'] = 'Niteit&auml;:';
  texts['available'] = 'saatavissa:';
  texts['first_due'] = 'ensimm&auml;isen er&auml;p&auml;iv&auml;:';
  texts['location'] = 'Sijainti';
  texts['restrictions'] = 'K&auml;ytt&ouml;rajoitukset';
  texts['electronic'] = 'Elektroninen aineisto';
  texts['holdings'] = 'Varastotiedot';
  texts['supplements'] = 'Lis&auml;numerot';
  texts['indexes'] = 'Hakemistot';
  texts['expand'] = 'N&auml;yt&auml;';
  texts['collapse'] = 'Piilota';
  texts['error'] = 'Tietoja ei saatavilla';
}

function addScript(i)
{
  $(this).after('<img src="/throbber.gif" alt="">');

  var url = $(this).attr('href');

  url = url.replace(/.*"(.*)\".*/, "$1");
  url = url.replace(/holdings\.cgi/, "holdings_proxy.cgi");
  url += '&callback=?';

  $.getJSON(url, function (data) { addHoldings(data) });
}

function addHoldings(data)
{
  var lib = data.holdings.lib;
  var error = data.holdings.error;

  if (error)
  {
    $("a[href^=javascript:open_window][href*=holdings.cgi][href*=" + lib + "] + img[src*=throbber]").remove();
    $("a[href^=javascript:open_window][href*=holdings.cgi][href*=" + lib + "]").after("<br>" + texts['error']);
    return;
  }

  var items = 0;
  var available = 0;
  var first_due = '';
  var have_holdings = 0;
  for (i in data.holdings.mfhd)
  {
    var mfhd = data.holdings.mfhd[i];
    items += (mfhd.item_count - 0);
    available += (mfhd.items_available - 0);
    if (mfhd.first_due_date && (!first_due || mfhd.first_due_date < first_due))
      first_due = mfhd.first_due_date;
    if (mfhd.location)
      have_holdings = 1;
  }
  if (first_due)
    first_due = first_due.replace(/(\d+)\.(\d+)\.(\d+)/, '$3.$2.$1');

  var holdings_html = '<br><img id="expand_' + lib + '" src="/plus.png" alt="' + texts['expand'] + '" onClick="showHoldings(\'' + lib + '\')"><img id="collapse_' + lib + '" src="/minus.png" alt="' +texts['collapse'] + '" onClick="hideHoldings(\'' + lib + '\')" style="display:none">&nbsp;';
  if (have_holdings && items == 0)
    holdings_html += texts['holdings']
  else
    holdings_html += texts['items'] + ' ' + items;
  if (items > 0)
  {
    holdings_html += ', ' + texts['available'] + ' ' + available;
    if (first_due)
      holdings_html += ', ' + texts['first_due'] + ' ' + first_due;
  }

  holdings_html += '<div id="holdings_' + lib + '" style="display: none; margin: 6px 0 6px 10px;">';

  for (i in data.holdings.mfhd)
  {
    var mfhd = data.holdings.mfhd[i];

    if (i > 0)
      holdings_html += '<br>';

    var item_locations = '';
    for (j in mfhd.item_locations)
    {
      var item_loc = mfhd.item_locations[j];
      if (item_locations)
        item_locations += "<br>\n";
      item_locations += item_loc.location + ' (' + texts['items'] + ' ' + item_loc.items;
      if (item_loc.items > 0)
      {
        item_locations += ', ' + texts['available'] + ' ' + item_loc.available;
        if (item_loc.first_due_date)
        {
          var first_due = item_loc.first_due_date.replace(/(\d+)\.(\d+)\.(\d+)/, '$3.$2.$1');
          item_locations += ', ' + texts['first_due'] + ' ' + first_due;
        }
      }
      item_locations += ')';
    }

    if (mfhd.location || item_locations)
    {
      if (mfhd.location && item_locations)
        item_locations += "<br>\n";
      holdings_html += '<strong>' + texts['location'] + '</strong><br>' + item_locations + mfhd.location + '<br>';
    }
    if (mfhd.restrictions)
      holdings_html += '<strong>' + texts['restrictions'] + '</strong><br>' + mfhd.restrictions + '<br>';

    if (mfhd.electronic_link)
    {
      holdings_html += '<strong>' + texts['electronic'] + '</strong><br>';
      if (!mfhd.electronic_link_text)
        mfhd.electronic_link_text = mfhd.electronic_link;
      if (mfhd.electronic_link_prefix)
        holdings_html += mfhd.electronic_link_prefix + ' ';
      holdings_html += '<a href=" ' + mfhd.electronic_link + '" target="_blank">' + mfhd.electronic_link_text + '</a>';
      if (mfhd.electronic_link_note)
        holdings_html += ' (' + mfhd.electronic_link_note + ')';
      holdings_html += '<br>';
    }

    if (mfhd.holdings_stmt || mfhd.textual_holdings_stmt)
    {
      holdings_html += '<strong>' + texts['holdings'] + '</strong><br>';
      if (mfhd.holdings_stmt)
        holdings_html += mfhd.holdings_stmt + '<br>';
      if (mfhd.textual_holdings_stmt)
        holdings_html += mfhd.textual_holdings_stmt + '<br>';
    }

    if (mfhd.supplements)
      holdings_html += '<strong>' + texts['supplements'] + '</strong><br>' + mfhd.supplements + '<br>';

    if (mfhd.indexes)
      holdings_html += '<strong>' + texts['indexes'] + '</strong><br>' + mfhd.indexes + '<br>';
  }
  holdings_html += '</div>';

  $("a[href^=javascript:open_window][href*=holdings.cgi][href*=" + lib + "] + img[src*=throbber]").remove();
  $("a[href^=javascript:open_window][href*=holdings.cgi][href*=" + lib + "]").after(holdings_html);

  if ($.cookie('expand_holdings_' + lib) == 'true')
    showHoldings(lib, 1);
}

function showHoldings(lib, instant)
{
  $("div[id=holdings_" + lib + "]").slideDown(instant ? 0 : "fast");
  $("img[id=expand_" + lib + "]").hide();
  $("img[id=collapse_" + lib + "]").show();
  $.cookie('expand_holdings_' + lib, 'true', { expires: 7 });
}

function hideHoldings(lib)
{
  $("div[id=holdings_" + lib + "]").slideUp("fast");
  $("img[id=expand_" + lib + "]").show();
  $("img[id=collapse_" + lib + "]").hide();
  $.cookie('expand_holdings_' + lib, null);
}

$(document).ready(function() {
   $("a[href^=javascript:open_window][href*=holdings.cgi]").each(addScript);
});

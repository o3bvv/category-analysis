#!/usr/bin/env python3

import json

import humanize

from jinja2 import Template


I_FILE_NAME  = "08_bookd_cat_tree.json"
O_FILE_NAME  = "10_bookd_cat_tree_view.html"

O_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Bookd Categories</title>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.2.1/themes/default/style.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css" />
    <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/purecss@2.1.0/build/pure-min.css" integrity="sha384-yHIFVG6ClnONEA5yB5DJXfW2/KC173DIQrYoZMEtBvGzmf0PKiGyNEqe9N6BNDBH" crossorigin="anonymous">

    <style>
      .badge {
        display: inline-block;
        padding: .1rem .4rem;
        font-size: 0.5em;
        border-radius: var(--border-radius);
        background: var(--code-background-color);
        color: var(--code-color);
        font-weight: var(--font-weight);
        line-height: initial;
      }
      #details-pane {
        border-left: var(--border-width) solid var(--card-border-color);
      }
      #details {
        padding: var(--typography-spacing-vertical); var(--block-spacing-horizontal);
      }
      #details hgroup {
        margin-bottom: calc(var(--typography-spacing-vertical) * 2);
      }
      #details .row {
        margin-bottom: var(--typography-spacing-vertical);
      }
    </style>
  </head>
  <body>

    <main class="container">
      <hgroup>
        <h1>Bookd Categories</h1>
        <h2>Explore topics and genres</h2>
      </hgroup>
      <article>
        <header>
          <div class="pure-g">
            <div class="pure-u-2-5">
              <a id="expand" href="#" role="button" class="secondary outline"><i class="fa-solid fa-up-right-and-down-left-from-center"></i> Expand All</a>
              <a id="collapse" href="#" role="button" class="secondary outline"><i class="fa-solid fa-down-left-and-up-right-to-center"></i> Collapse All</a>
            </div>
            <div class="pure-u-3-5">
              <input id="search" type="search" name="search" placeholder="Search" />
            </div>
          </div>
        </header>
        <div class="pure-g" id="viewport">
          <figure class="pure-u-14-24">
            <div id="jstree"></div>
          </figure>
          <aside class="pure-u-10-24" id="details-pane">
            <div id="details">
              <i>Select an item to see details.</i>
            </div>
          </aside>
        </div>
      </article>
    </main>

	  <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jstree/3.2.1/jstree.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/sticky-sidebar/3.3.1/sticky-sidebar.min.js" integrity="sha512-iVhJqV0j477IrAkkzsn/tVJWXYsEqAj4PSS7AG+z1F7eD6uLKQxYBg09x13viaJ1Z5yYhlpyx0zLAUUErdHM6A==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
    <script>
      $(function () {
        var site_root_url       = "https://www.bookdepository.com/category/";
        var category_url_suffix = "/browse/viewmode/all";

        var time_out = false;

        function format_url(cid) {
          return site_root_url + cid + category_url_suffix;
        }

        function build_details(data) {
          var heading = $("<h3/>").text(data.title);

          var grid = $("<div/>", { "class": "pure-g" }).append([
            $("<div/>", {"class": "row pure-u-1-2"}).text("Count estimate:"),
            $("<div/>", {"class": "row pure-u-1-2"}).text(data.count),
            $("<div/>", {"class": "row pure-u-1"}).html(
              " <a href='" + format_url(data.cid) + "' target='_blank'>Visit <i class='fa-solid fa-up-right-from-square fa-2xs'></i></a>."
            ),
          ]);

          // Root
          return [heading, grid];
        }

        $("#jstree").jstree({
          "plugins": ["types", "sort", "search"],
          "types": {
            "leaf": {
              "icon": "fa-solid fa-tag"
            },
            "non-leaf": {
              "icon": "fa-solid fa-tags"
            }
          },
          "core": {
            "themes" : {
              "variant" : "large",
            },
            "data": {{ tree_data }}
          }
        })
        .on("select_node.jstree", function (event, data) {
          $("#details").empty().append(build_details(data.node.data));
        })
        .bind("ready.jstree", function (event, data) {

          var sidebar = new StickySidebar('#details-pane', {
            topSpacing: 20,
            containerSelector: '#viewport',
            innerWrapperSelector: '#details'
          });

          $("#expand").click(function(e) {
            e.preventDefault();
            if (time_out) { clearTimeout(time_out); }
            time_out = setTimeout(function () {
              $('#jstree').jstree(true).open_all();
              return false;
            }, 250);
          });

          $("#collapse").click(function(e) {
            e.preventDefault();
            if (time_out) { clearTimeout(time_out); }
            time_out = setTimeout(function () {
              $('#jstree').jstree(true).close_all();
              return false;
            }, 250);
          });

          $('#search').keyup(function () {
            if (time_out) { clearTimeout(time_out); }
            var v = $('#search').val().trim();
            time_out = setTimeout(function () {
              $('#jstree').jstree(true).search(v);
            }, 250);
          });

        });
      });

    </script>
  </body>
</html>
""")


def prepare_tree_node(node: dict) -> dict:
  count = node['data'].get('count') or 0

  children = node.get('children') or []
  children = [
    prepare_tree_node(child) for child in children
  ]

  result = {
    'id':   node['id'],
    'text': f"{node['data']['title']} <span class='badge'>{humanize.metric(count) if count else count}</span>",
    'type': ("leaf" if not children else "non-leaf"),
    'data': {
      'title': node['data']['title'],
      'cid':   node['id'],
      'count': humanize.intcomma(count),
    },
    'children': children,
  }

  return result


def prepare(catalog: list[dict]) -> list[dict]:
  return [prepare_tree_node(category) for category in catalog]


def main() -> None:
  with open(I_FILE_NAME, 'rt') as f:
    catalog = json.load(f)

  tree_data = prepare(catalog)

  with open(O_FILE_NAME, 'wt') as f:
    f.write(O_TEMPLATE.render(
      tree_data = json.dumps(tree_data),
    ))


if __name__ == "__main__":
  main()

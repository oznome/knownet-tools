import sys, os, time, requests
import json
import geojson
import ipyleaflet as ll
import ipywidgets as widgets
from ipywidgets import interact, interactive, fixed, interact_manual, Layout, HBox, VBox, HTML
from IPython.display import clear_output, Javascript
import IPython.display as idisplay
from IPython.core.interactiveshell import InteractiveShell

class KnowMapWidget:

    def __init__(self):
        self.start = 0
        self.added_layer = None
        self.layers = []
        self._result_data = None
        self.last_search = ''
        self.length = 0
        self.result_datas = []
        self.layer_widget = None
        self.next_button_widget = widgets.Button(
            description='Next Results',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
        )
        self.next_button_widget.on_click(self.on_next)
        self.previous_button_widget = widgets.Button(
            description='Previous Results',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
        )
        self.previous_button_widget.on_click(self.on_previous)
        self.wait_widget = widgets.HTML(value="""
                                        <script>window.alert("Hello");</script>
                                        <style>.loader {
                                            border: 16px solid #f3f3f3; /* Light grey */
                                            border-top: 16px solid #3498db; /* Blue */
                                            border-radius: 50%;
                                            width: 20px;
                                            height: 20px;
                                            animation: spin 2s linear infinite;
                                        }

                                        @keyframes spin {
                                            0% { transform: rotate(0deg); }
                                            100% { transform: rotate(360deg); }
                                        }</style>
                                        <div class="loader"></div>
                                        """)
        self.result_name = None
        self.hbox_display = False
        self.hbox=widgets.HBox()
        self.vbox=widgets.VBox()
        self.selected_label = widgets.Label(value="Nothing Selected", placeholder='Nothing Selected',
                                            description='Selected Data',
                                            layout=Layout(width='100%'),
                                            disabled=False)
        self.map = ll.Map(center=[-25.752396, 134.121094], zoom=4)
        self.show()

    def on_next(self, button):
        self.start = self.start + 5
        self.search_knowledge(self.last_search)

    def on_previous(self, button):
        self.start = self.start - 5
        self.search_knowledge(self.last_search)

    def post_provenance(self, pid):
        shell = InteractiveShell.instance()
        headers = { 'X-Auth-Token': 'I8Ob79Hri10fjAEviC5CEaaboCFcnzbxtIvN2mFcvNH',
                    'X-User-Id' : 'LduPNdS7xzthBtGPr' }
        print(pid)
        r = requests.post("http://kn.csiro.au/api/playlist/4siRHNmrB7rKkMzx6",
                          json={"items": [pid]},
                          headers=headers)

        from time import gmtime, strftime
        current_time = strftime("%Y-%m-%dT%H:%M:%S+00:00", gmtime())

        try:
            git_url =  shell.user_ns['PROVENANCE_GIT_URL']
        except:
            git_url = 'Unknown Repository'

        try:
            notebook_name =  shell.user_ns['NOTEBOOK_NAME']
        except:
            notebook_name = 'Unknown Notebook'

        print("Creating JSON")
        provenance_json = {
            "activity": {
                "startedAtTime": current_time,
                "comment": "Ran a workflow with playlist resource using " + notebook_name + " from " + git_url,
                "type": "provenance",
                "@graph": [
                    {
                        "@id": "http://example.com/id/prov/123",
                        "@type": "prov:Activity",
                        "startedAtTime": current_time,
                        "endedAtTime": current_time
                    },
                    {
                        "@id": notebook_name,
                        "@type": "prov:Entity",
                        "generation": { "activity": "http://example.com/id/prov/123" }
                    }
                ]
            }
        }
        print("Created JSON")

        r = requests.post("http://kn.csiro.au/api/playlist/4siRHNmrB7rKkMzx6",
                          json=provenance_json, headers = headers)

        print(r.status_code)

    def test_method(self):
        from IPython.core.interactiveshell import InteractiveShell
        shell = InteractiveShell.instance()
        print(shell.all_ns_refs)

    @property
    def result_data(self):
        self.post_provenance(self.result_pid)
        return self._result_data

    def add_click_handler(self, layer):
        def click_handler(properties, event):
            #print(self.result_datas['properties'].keys())
            self._result_data = self.result_datas[properties['selected_id']]
            self.result_pid = properties['url']
            self.result_name = properties['name']
            self.selected_label.value = self.result_name
        layer.on_click(click_handler)

    def search_knowledge(self, search):
        clear_output()
        self.result_datas = []
        self.layers = []
        self.hbox.children = (self.search_widget, self.wait_widget)
        limit = 5
        # a new search reset everything
        if search != self.last_search:
            start = 0
            limit = 5
            self.start = start
        # set start to object start as this can be modified by button clicks
        start = self.start
        search_string = 'http://kn.csiro.au/api/search/feature?q={search}&_start={start}&_limit={limit}'.format(search=search, start=start, limit=limit)
        next_search = 'http://kn.csiro.au/api/search/feature?q={search}&_start={limit}&_limit=1'.format(search=search, limit=limit)
        self.last_search = search
        try:
            data = requests.get(search_string)
        except:
            pass
        try:
            next_data = requests.get(search_string)
        except:
            pass
        #self.hbox.children = (self.search_widget, self.layer_widget)
        self.length = len(data.json()) -1
        i = 0
        for result in data.json():
            name = "Unknown"
            if "name" in result.keys():
                name  = result['name']
            pid = result['pid']
            geojson_url = pid + '?_format=json'
            result = requests.get(geojson_url)
            data = result.json()
            self.result_datas.append(data)
            text = result.text
            feature = data
            if not 'properties' in feature:
                feature['properties'] = {}
                feature['properties']['style'] = {
                    'color': 'grey',
                    'weight': 1,
                    'fillColor': 'grey',
                    'fillOpacity': 0.5
                }
            feature['properties']['selected_id'] = i
            feature['properties']['name'] = name
            feature['properties']['url'] = pid

            layer = ll.GeoJSON(data=data, hover_style={'fillColor': 'red'})
            self.add_click_handler(layer)
            self.layers.append(layer)
            i += 1
        if self.layer_widget != None:
            self.layer_widget.close()
        if self.length < 0:
            self.length = 0
        self.show_layer(1)
        self.layer_widget = interactive(self.show_layer, index=widgets.IntSlider(description='Results (' + str(self.length + 1) + ')', min=1, max=self.length + 1, step=1, value=1))
        self.hbox.children = (self.search_widget, self.layer_widget, self.previous_button_widget, self.next_button_widget)

    def show_layer(self, index):
        index = index - 1
        if len(self.layers) < 1:
            return
        if self.added_layer != None:
            self.map.remove_layer(self.added_layer)
        self.added_layer = self.layers[index]
        self.map.add_layer(self.added_layer)

    def show(self):
        self.search_widget = interactive(self.search_knowledge, search='victoria')
        self.hbox.children = (self.search_widget,)
        idisplay.display(self.hbox)
        idisplay.display(self.vbox)
        self.vbox.children = (self.map, self.selected_label)

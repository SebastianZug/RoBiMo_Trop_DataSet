importScripts("https://cdn.jsdelivr.net/pyodide/v0.22.1/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/0.14.4/dist/wheels/bokeh-2.4.3-py3-none-any.whl', 'https://cdn.holoviz.org/panel/0.14.4/dist/wheels/panel-0.14.4-py3-none-any.whl', 'pyodide-http==0.1.0', 'holoviews>=1.15.4', 'hvplot', 'numpy', 'pandas', 'pathlib']
  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  
import asyncio

from panel.io.pyodide import init_doc, write_doc

init_doc()

#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from pathlib import Path
import numpy as np
import panel as pn

pn.extension('tabulator')

#import cartopy.crs as ccrs
#import geoviews as gv 
#import pyproj

#pn.extension(sizing_mode="stretch_width")

import hvplot.pandas


# In[2]:


input_data_folder_base = Path("../results/")
input_data_folder = Path.cwd() / input_data_folder_base
overall_collection_file_name = "overall_collection_2023.p"
key_parameter_file_name = "key_parameter_2023.p"
cluster_positions_file_name = "cluster_positions_2023.p"
print(f"Reading raw pandas files from \\n    {input_data_folder}")

output_folder_base = Path("../html/")
output_image_folder = output_folder_base / Path("./images/")
print(f"Writing website information to \\n    {output_folder_base}")


# In[3]:


# cache data to improve dashboard performance
if 'data' not in pn.state.cache.keys():
    #df_key_param = pd.read_pickle(input_data_folder / key_parameter_file_name)
    #df_key_param = pd.read_pickle("https://api.allorigins.win/get?url=https://github.com/SebastianZug/RoBiMo_Trop_DataSet/blob/main/results/key_parameter_2023.p?raw=true")
    #df_key_param = pd.read_pickle("https://api.allorigins.win/raw?url=https://github.com/SebastianZug/RoBiMo_Trop_DataSet/blob/main/results/key_parameter_2023.p?raw=true")

    df_key_param = pd.read_pickle("https://sebastianzug.github.io/RoBiMo_Trop_DataSet/results/key_parameter_2023.p?raw=true")

    pn.state.cache['data'] = df_key_param.copy()
else: 
    df_key_param = pn.state.cache['data']


# In[4]:


df_key_param


# In[10]:


# Make DataFrame Pipeline Interactive
idf = df_key_param.interactive()


# In[11]:


select_lake = pn.widgets.Select(
    name='Location',
    value="Balbina",
    options=list(df_key_param.experiment_location.unique())
)

select_position = pn.widgets.Select(
    name="Measurement",
    value=df_key_param.position.unique()[0],
    options=df_key_param[df_key_param.experiment_location==select_lake.value].position.unique().tolist()
)

@pn.depends(select_lake.param.value, watch=True)
def _update_lake(select_lake):
    positions = list(df_key_param[df_key_param.experiment_location==select_lake]\
                            .position.unique())
    select_position.options = positions
    select_position.value = positions[0]


# In[12]:


data_pipeline_overview = (
    idf[
        (idf.experiment_location == select_lake ) &
        (idf.position == select_position)
    ]\
           [['start', 'end', 'CO2_min', 'CO2_max', 'PAR_min',  'PAR_max']]\
           .describe(datetime_is_numeric=True)\
           .loc[['mean', 'std', 'min', 'max'],:]
)

# data_pipeline_overview


# In[13]:


data_pipeline_all = (
    idf[
        (idf.experiment_location == select_lake ) &
        (idf.position == select_position)
    ]\
        [['start', 'end', 'hdop_max', 'nsats_min', 'CO2_min', 'CO2_max', 'PAR_min',  'PAR_max']]
)

#data_pipeline_all


# In[14]:


#co_plot=selected_data_pipeline.hvplot(use_index=True, y='CO2(ppm)', title="CO_2 concentration")
#pressure_plot=selected_data_pipeline.hvplot(use_index=True, y='pressure in(mbar)', title="Pressure in")


# In[15]:


table_overview = data_pipeline_overview.pipe(pn.widgets.Tabulator, pagination="remote", title="Aggregated key parameters of the position")
table_all = data_pipeline_all.pipe(pn.widgets.Tabulator, pagination="remote", title="Parameter of all measurements at this position")


# In[ ]:


#template = pn.template.FastListTemplate(
#    title = "RoBiMo 2023 - Data exploration",
#    sidebar =[pn.pane.Markdown("# Select the relevant lake and measurement"),
#              select_lake,
#              select_file],
#    main=[pn.Row(
#            pn.Column(
#               position_plot.panel(width=500, margin=(0,25))
#            ),
#            pn.Column(
#               table.panel(width=1000, margin=(0,25))
#            )
#         ),
#         pn.Row(
#            pn.Column(
#               pressure_plot.panel(width=600, margin=(0,25))
#            ),
#            pn.Column(
#               co_plot.panel(width=600, margin=(0,25))
#            )
#         )     
#    ]
#)

template = pn.template.FastListTemplate(
    title = "RoBiMo 2023 - Data overview",
    sidebar =[pn.pane.Markdown("# Selection"),
              select_lake,
              select_position],
    main=[pn.Row(
               pn.pane.Markdown("Aggregated key parameters of the position"),
               table_overview.panel(width=1000)
         ),
         pn.Row(
               pn.pane.Markdown("Parameter of all measurements at this position"),
               table_all.panel(width=1000)
         )     
    ]
)

#template.show()
template.servable();


# In[ ]:






await write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.runPythonAsync(`
    import json

    state.curdoc.apply_json_patch(json.loads('${msg.patch}'), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads("""${msg.location}""")
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()
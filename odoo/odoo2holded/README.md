# odoo2holded

## Name
odoo2holded

## Description
It is an Odoo plugin which allows you to copy data into Holded automatically using its API.

## Installation
To install this addon you have to insert the folder in the path which odoo has configured to detect installed plugins. 
You can find this out by opening the odoo configuration file "odoo.conf" with any text editor. Normally it is in odoo 
C:\odoo16\server\odoo.conf, once opened look for the line that says "addons_path = c:\odoo16\server\odoo\addons" by 
default.
It is recommended to create a "custom_addons" folder, change the path in the configuration file to something 
similar to"addons_path = c:\odoo16\server\odoo\custom_addons" and insert your custom addons there.

Then you need to reinitialise de Odoo service and then in odoo update the app list, with this our plugin should appear.
Now is the moment to install it.

Now you can access our addon via the Odoo dropdown menu in the top left corner clicking on "Odoo2Holded". This will 
redirect you to the first section of the addon "Products" by default. Now we need to configure the addon, to do this we 
need to go to the "Settings" section from the menu bar to add the Holded API KEY we want to work with and configure the 
Cron Job for automatic synchronizations. All fields are required to work correctly. Once we configure the addon it will 
start working.

## Usage
This plugin synchronizes Odoo and Holded automatically using a configurable cron job. The only thing you need to do once 
configured as explained in the installation section is to create your contacts, products and invoice records in Odoo and 
then wait for the next synchronization. Alternatively, you can sync manually by clicking on the "Sync All" button next to
the configuration menu. You can access each of the sections via the plugin's menu bar, which will not only take you to the 
desired section, but will also refresh the records, showing you the data that exists in Holded at that moment. 
Alternatively, if a record is selected, a "Syncronize" button will appear, which will refresh the section in the same way.

## Support
https://whitewall-ers.com

## Authors and acknowledgment
Jose Miguel García Navarro
Whitewall Software

## License
OPL-1

## Project status
Active

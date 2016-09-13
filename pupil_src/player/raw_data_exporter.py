'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2016  Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import os
import csv
from itertools import chain
import logging
from plugin import Plugin
from pyglui import ui
# logging
logger = logging.getLogger(__name__)

import cPickle as pickle

class Raw_Data_Exporter(Plugin):
    '''
    pupil_positions.csv
    keys:
        timestamp - timestamp of the source image frame
        id - 0 or 1 for left/right eye
        #data made available by the `3d c++` detector
        diameter_3d - diameter of the pupil scaled to mm based on anthropomorphic avg eye ball diameter and corrected for perspective.
        '''
    def __init__(self,g_pool):
        super(Raw_Data_Exporter, self).__init__(g_pool)

    def init_gui(self):
        self.menu = ui.Scrolling_Menu('Raw Data Exporter')
        self.g_pool.gui.append(self.menu)

        def close():
            self.alive = False

        self.menu.append(ui.Button('Close',close))
        self.menu.append(ui.Info_Text('Export Raw Pupil Capture data into .csv files.'))
        self.menu.append(ui.Info_Text('Select your export frame range using the trim marks in the seek bar. This will affect all exporting plugins.'))
        self.menu.append(ui.Info_Text('Select your export frame range using the trim marks in the seek bar. This will affect all exporting plugins.'))
        self.menu.append(ui.Text_Input('in_mark',getter=self.g_pool.trim_marks.get_string,setter=self.g_pool.trim_marks.set_string,label='frame range to export'))
        self.menu.append(ui.Info_Text("Press the export button or type 'e' to start the export."))

    def deinit_gui(self):
        if self.menu:
            self.g_pool.gui.remove(self.menu)
            self.menu = None


    def on_notify(self,notification):
        if notification['subject'] is "should_export":
            self.export_data(notification['range'],notification['export_dir'])

        
    def export_data(self,export_range,export_dir,rec_dir):
        with open(os.path.join(export_dir,'pupil_postions.csv'),'wb') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')

            csv_writer.writerow(('timestamp',
                                    'id',
                                    'diameter_3d'))

            for p in list(chain(*self.g_pool.pupil_positions_by_frame[export_range])):
                data_2d = [ '%s'%p['timestamp'],  #use str to be consitant with csv lib.
                            p['id'] ]

                try:
                    data_3d =   [   p['diameter_3d'] ]
                except KeyError as e:
                    data_3d = [None,]*21
                row = data_2d + data_3d
                csv_writer.writerow(row)
            logger.info("Created 'pupil_positions.csv' file.")

        with open(os.path.join(rec_dir,'rb') as fh:
            data=fh.read()
        d=pickle.loads(data)
        d1=d['notifications']
        d2=str(d1)
        d3=open(os.path.join(export_dir,'audio_data.txt','w')
        d3.write(d2)
        d3.close()
            

    def get_init_dict(self):
        return {}

    def cleanup(self):
        self.deinit_gui()

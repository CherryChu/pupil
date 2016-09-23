'''
(*)~----------------------------------------------------------------------------------
 Pupil - eye tracking platform
 Copyright (C) 2012-2016  Pupil Labs

 Distributed under the terms of the GNU Lesser General Public License (LGPL v3.0).
 License details are in the file license.txt, distributed as part of this software.
----------------------------------------------------------------------------------~(*)
'''

import os,sys, platform, errno, getpass
import csv
import numpy as np
from itertools import chain
import logging
from time import strftime,localtime,time,gmtime
from plugin import Plugin
from pyglui import ui
# loggingwrite into csv file
logger = logging.getLogger(__name__)
import cPickle as pickle
from exporter import export
import exporter

def get_auto_name():
    return strftime("%Y_%m_%d", localtime())

class Raw_Data_Exporter(Plugin):
    '''
    pupil_positions.csv
    keys:
        timestamp - timestamp of the source image frame
        id - 0 or 1 for left/right eye
        diameter_3d - diameter of the pupil scaled to mm based on anthropomorphic avg eye ball diameter and corrected for perspective.
        '''
    def __init__(self,g_pool):
        super(Raw_Data_Exporter, self).__init__(g_pool)
        
        self.default_path = os.path.expanduser('~/')
        self.session_name = get_auto_name()
        add_path=os.path.join(self.default_path,'Desktop','pupil','recordings',self.session_name)
        self.source_dir = add_path
        
    def init_gui(self):
        self.menu = ui.Scrolling_Menu('Raw Data Exporter')
        self.g_pool.gui.append(self.menu)

        def close():
            self.alive = False

        self.menu.append(ui.Button('Close',close))
        self.menu.append(ui.Info_Text('Export Raw Pupil Capture data into .csv files.'))
        self.menu.append(ui.Info_Text('Select your export frame range using the trim marks in the seek bar. This will affect all exporting plugins.'))
        self.menu.append(ui.Text_Input('in_mark',getter=self.g_pool.trim_marks.get_string,setter=self.g_pool.trim_marks.set_string,label='frame range to export'))
        self.menu.append(ui.Info_Text("Press the export button or type 'e' to start the export."))
        self.menu.append(ui.Info_Text("Please complete the full path to export markerfile."))
        self.menu.append(ui.Text_Input('source_dir',self,setter=self.set_src_dir,label='Path'))

    def deinit_gui(self):
        if self.menu:
            self.g_pool.gui.remove(self.menu)
            self.menu = None

    def set_src_dir(self,new_dir):
        new_dir = new_dir
        new_dir = os.path.expanduser(new_dir)
        if os.path.isdir(new_dir):
            self.source_dir = new_dir
        else:
            logger.warning('"%s" is not a directory'%new_dir)
            return
            
    def on_notify(self,notification):
        if notification['subject'] is "should_export":
            self.export_data(notification['range'],notification['export_dir'])

    def export_data(self,export_range,export_dir):

        with open(os.path.join(export_dir,'pupil_postions.csv'),'wb') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')

            csv_writer.writerow(('timestamp',
                                    'id',
                                    'diameter_3d'))

            for p in list(chain(*self.g_pool.pupil_positions_by_frame[export_range])):
                data_2d = [ '%s'%p['timestamp'],  #use str to be consitant with csv lib.
                            p['id'] ]

                try:
                    data_3d =   [   p['diameter_3d']     ]
                except KeyError as e:
                    data_3d = [None,]*21
                row = data_2d + data_3d
                csv_writer.writerow(row)
            logger.info("Created 'pupil_positions.csv' file.")
           
        with open(os.path.join(export_dir,'marker.csv'),'wb') as markerfile:
            #with open(os.path.join(exporter.export(rec_dir),'pupil_data'),'rb') as fh:
            try:
                with open(os.path.join(self.source_dir,'pupil_data'),'rb') as fh:
                    data=fh.read()
                d=pickle.loads(data)
                d1=d['notifications']
                writer=csv.writer(markerfile,delimiter=',')
                writer.writerow(d1)
                logger.info("Created 'marker.csv' file.")
            except IOError:
                logger.error("Did not complete the full path.")
                return False
             
        with open(os.path.join(export_dir,'gaze_postions.csv'),'wb') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',')
            csv_writer.writerow(("timestamp",
                                 "index",
                                 "confidence",
                                 "norm_pos_x",
                                 "norm_pos_y",
                                 "base_data",
                                 "gaze_point_3d_x",
                                 "gaze_point_3d_y",
                                 "gaze_point_3d_z",
                                 "eye_center0_3d_x",
                                 "eye_center0_3d_y",
                                 "eye_center0_3d_z",
                                 "gaze_normal0_x",
                                 "gaze_normal0_y",
                                 "gaze_normal0_z",
                                 "eye_center1_3d_x",
                                 "eye_center1_3d_y",
                                 "eye_center1_3d_z",
                                 "gaze_normal1_x",
                                 "gaze_normal1_y",
                                 "gaze_normal1_z"
                                     ) )

            for g in list(chain(*self.g_pool.gaze_positions_by_frame[export_range])):
                data = ['%s'%g["timestamp"],g["index"],g["confidence"],g["norm_pos"][0],g["norm_pos"][1]," ".join(['%s-%s'%(b['timestamp'],b['id']) for b in g['base_data']]) ] #use str on timestamp to be consitant with csv lib.

                #add 3d data if avaiblable
                if g.get('gaze_point_3d',None) is not None:
                    data_3d = [g['gaze_point_3d'][0],g['gaze_point_3d'][1],g['gaze_point_3d'][2]]

                    #binocular
                    if g.get('eye_centers_3d',None) is not None:
                        data_3d += g['eye_centers_3d'].get(0,[None,None,None])
                        data_3d += g['gaze_normals_3d'].get(0,[None,None,None])
                        data_3d += g['eye_centers_3d'].get(1,[None,None,None])
                        data_3d += g['gaze_normals_3d'].get(1,[None,None,None])
                    #monocular
                    elif g.get('eye_center_3d',None) is not None:
                        data_3d += g['eye_center_3d']
                        data_3d += g['gaze_normal_3d']
                        data_3d += [None,]*6
                else:
                    data_3d = [None,]*15
                data +=data_3d
                csv_writer.writerow(data)
            logger.info("Created 'gaze_positions.csv' file.")


        with open(os.path.join(export_dir,'pupil_gaze_postions_info.txt'),'w') as info_file:
            info_file.write(self.__doc__)


    def get_init_dict(self):
        return {}

    def cleanup(self):
        self.deinit_gui()

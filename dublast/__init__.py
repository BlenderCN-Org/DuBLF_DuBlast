# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "DuBlast",
    "author" : "Nicolas 'Duduf' Dufresne",
    "blender" : (2, 81, 0),
    "version" : (1,1,0),
    "location" : "Render Properties, 3D View > View menu, 3D View > Sidebar (N) > Tool tab",
    "description" : "Create playblasts: Quickly render and play viewport animation.",
    "warning" : "",
    "category" : "Animation",
    "wiki_url": "http://dublast-docs.rainboxlab.org"
}

import bpy # pylint: disable=import-error
import os

from . import (
    dublf,
)

class DUBLAST_settings( bpy.types.PropertyGroup ):
    """Playblast settings for a scene."""

    use_camera: bpy.props.BoolProperty( name= "Use scene camera", description= "Renders using either the scene camera or the current viewport.", default= False)

    resolution_percentage: bpy.props.FloatProperty( name= "Resolution %", description= "Overrides the rendering resolution percentage for the playblast", default = 25.0, min=0.0, max= 100.0, precision=0, subtype='PERCENTAGE')
    
    use_scene_frame_range: bpy.props.BoolProperty( name= "Use scene frame range", description= "Uses the frame range of the scene.", default= True)
    frame_start: bpy.props.IntProperty( name= "Frame Start", description= "Overrides the frame start for the playblast", default = 1, min=0 )
    frame_end: bpy.props.IntProperty( name= "Frame End", description= "Overrides the frame end for the playblast", default = 250, min=0 )
    frame_step: bpy.props.IntProperty( name= "Frame Step", description= "Overrides the frame step for the playblast", default = 1, min=1 )

    filepath: bpy.props.StringProperty( name="Output Path", description="Directory/name to save playblasts", subtype="FILE_PATH")
    use_scene_name: bpy.props.BoolProperty( name= "Use scene name", description= "Uses the name of the scene when saving file.", default= True)
    use_scene_path: bpy.props.BoolProperty( name= "Use scene path", description= "Saves the file next to the scene file.", default= True)

    file_format: bpy.props.EnumProperty(
        items = [
            ('PNG', "PNG", "Output image in PNG format.", 'FILE_IMAGE', 1),
            ('JPEG', "JPEG", "Output image in JPEG format.", 'FILE_IMAGE', 2),
            ('AVI_JPEG', "AVI JPEG", "Output video in AVI JPEG format.", 'FILE_MOVIE', 3),
            ('MP4', "MP4", "Output video in MP4 format, but optimized for animation playblast.", 'FILE_MOVIE', 4)
        ],
        name = "File Format",
        description= "File format to save the playblasts",
        default= 'MP4'
        )

    color_mode: bpy.props.EnumProperty(
        items = [
            ('BW', "BW", "Images get saved in 8 bits grayscale.", '', 1),
            ('RGB', "RGB", "Images are saved with RGB (color) data.", '', 2),
            ('RGBA', "RGBA", "Images are saved with RGB and Alpha data (if supported).", '', 3)
        ],
        name = "Color",
        description= "Choose BW for saving grayscale images, RGB for saving red, green and blue channels, and RGBA for saving red, green, blue and alpha channels",
        default= 'RGB'
        )

    color_mode_no_alpha: bpy.props.EnumProperty(
        items = [
            ('BW', "BW", "Images get saved in 8 bits grayscale.", '', 1),
            ('RGB', "RGB", "Images are saved with RGB (color) data.", '', 2)
        ],
        name = "Color",
        description= "Choose BW for saving grayscale images, RGB for saving red, green and blue channels.",
        default= 'RGB'
        )
    
    compression: bpy.props.IntProperty( name= "Compression", description= "Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output", default = 15, min=0, max = 100 )
    quality: bpy.props.IntProperty( name= "Quality", description= "Quality for image formats that support lossy compression", default = 50, min=0, max = 100 )

    use_stamp: bpy.props.BoolProperty( name= "Burn Metadata into image", description= "Render the stamp info text in the rendered image.", default= True)

class DUBLAST_PT_playblast_settings(bpy.types.Panel):
    bl_label = "Playblast"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout

        # Add settings for the current scene
        playblast_settings = bpy.context.scene.playblast

        b = layout.box()
        b.prop( playblast_settings, "use_camera" )

        b = layout.box()
        b.prop( playblast_settings, "resolution_percentage", slider = True )

        b = layout.box()

        b.prop( playblast_settings, "use_scene_frame_range" )
        if not playblast_settings.use_scene_frame_range:
            b.prop( playblast_settings, "frame_start" )  
            b.prop( playblast_settings, "frame_end" )       
            b.prop( playblast_settings, "frame_step" ) 

        b = layout.box()

        b.prop( playblast_settings, "use_scene_path")
        if not playblast_settings.use_scene_path:
            b.prop( playblast_settings, "use_scene_name")
            b.prop( playblast_settings, "filepath" )
        b.prop( playblast_settings, "file_format" )
        if playblast_settings.file_format == 'PNG':
            b.prop( playblast_settings, "color_mode" )
            b.prop( playblast_settings, "compression", slider = True )
        else:
            b.prop( playblast_settings, "color_mode_no_alpha" )
            b.prop( playblast_settings, "quality", slider = True )

        b = layout.box()

        b.prop( playblast_settings, "use_stamp" )

class DUBLAST_OT_playblast( bpy.types.Operator ):
    """Renders and plays an animation playblast."""
    bl_idname = "render.playblast"
    bl_label = "Animation Playblast"
    bl_description = "Render and play an animation playblast."
    bl_option = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):

        scene = context.scene
        playblast = scene.playblast
        render = scene.render

        # Keep previous values
        resolution_percentage = render.resolution_percentage
        resolution_x = render.resolution_x
        resolution_y = render.resolution_y
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        frame_step = scene.frame_step
        filepath = render.filepath
        file_format = render.image_settings.file_format
        color_mode = render.image_settings.color_mode
        quality = render.image_settings.quality
        compression = render.image_settings.compression
        use_stamp = render.use_stamp
        stamp_font_size = render.stamp_font_size
        codec = render.ffmpeg.codec
        scformat = render.ffmpeg.format
        constant_rate_factor = render.ffmpeg.constant_rate_factor
        ffmpeg_preset = render.ffmpeg.ffmpeg_preset
        gopsize = render.ffmpeg.gopsize
        audio_codec = render.ffmpeg.audio_codec
        audio_bitrate = render.ffmpeg.audio_bitrate

        # Set playblast settings
        render.resolution_percentage = playblast.resolution_percentage
        while ( render.resolution_x * playblast.resolution_percentage / 100 ) % 2 != 0:
            render.resolution_x = render.resolution_x + 1
        while ( render.resolution_y * playblast.resolution_percentage / 100 ) % 2 != 0:
            render.resolution_y = render.resolution_y + 1

        if not playblast.use_scene_frame_range:
            scene.frame_start = playblast.frame_start
            scene.frame_end = playblast.frame_end
            scene.frame_step = playblast.frame_step

        blend_filepath = bpy.data.filepath
        blend_dir = os.path.dirname(blend_filepath)
        blend_file = bpy.path.basename(blend_filepath)
        blend_name = os.path.splitext(blend_file)[0]

        if playblast.use_scene_path and not blend_filepath == "":
            playblast.filepath = blend_dir + "/"
            playblast.use_scene_name = True
        if playblast.filepath == "":
            playblast.filepath = render.filepath
        
        if playblast.use_scene_name:
            if not scene.name == "Scene" or blend_name == "":
                name = scene.name + "_"
            else:
                name = blend_name + "_"
            if not playblast.filepath.endswith("/") and not playblast.filepath.endswith("\\"):
                playblast.filepath = playblast.filepath + "/"
            render.filepath = playblast.filepath + name
        else:
            render.filepath = playblast.filepath
            
        if playblast.file_format == 'MP4':
            render.image_settings.file_format = 'FFMPEG'
            render.ffmpeg.format = 'MPEG4'
            render.ffmpeg.codec = 'H264'
            if playblast.quality < 17:
                render.ffmpeg.constant_rate_factor = 'LOWEST'
            elif playblast.quality < 33:
                render.ffmpeg.constant_rate_factor = 'VERYLOW'
            elif playblast.quality < 50:
                render.ffmpeg.constant_rate_factor = 'LOW'
            elif playblast.quality < 67:
                render.ffmpeg.constant_rate_factor = 'MEDIUM'
            elif playblast.quality < 85:
                render.ffmpeg.constant_rate_factor = 'HIGH'
            elif playblast.quality < 100:
                render.ffmpeg.constant_rate_factor = 'PERC_LOSSLESS'
            else:
                render.ffmpeg.constant_rate_factor = 'LOSSLESS'
            render.ffmpeg.ffmpeg_preset = 'REALTIME'
            render.ffmpeg.gopsize = 1
            render.ffmpeg.audio_codec = 'AAC'
            render.ffmpeg.audio_bitrate = 128
        else:
            render.image_settings.file_format = playblast.file_format
        if playblast.file_format == 'PNG':
            render.image_settings.color_mode = playblast.color_mode
        else:
            render.image_settings.color_mode = playblast.color_mode_no_alpha
        render.image_settings.quality = playblast.quality
        render.image_settings.compression = playblast.compression

        render.use_stamp = playblast.use_stamp
        render.stamp_font_size = render.stamp_font_size * playblast.resolution_percentage / 100
        
        # Render and play
        bpy.ops.render.opengl( animation = True, view_context = not playblast.use_camera )
        bpy.ops.render.play_rendered_anim( )

        # Re-set settings
        render.resolution_percentage = resolution_percentage
        render.resolution_x = resolution_x
        render.resolution_y = resolution_y
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        scene.frame_step = frame_step
        render.filepath = filepath
        render.image_settings.file_format = file_format
        render.image_settings.color_mode = color_mode
        render.image_settings.quality = quality
        render.image_settings.compression = compression
        render.use_stamp = use_stamp
        render.stamp_font_size = stamp_font_size
        render.ffmpeg.format = scformat
        render.ffmpeg.codec = codec
        render.ffmpeg.constant_rate_factor = constant_rate_factor
        render.ffmpeg.ffmpeg_preset = ffmpeg_preset 
        render.ffmpeg.gopsize = gopsize
        render.ffmpeg.audio_codec = audio_codec
        render.ffmpeg.audio_bitrate = audio_bitrate

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.separator()
    self.layout.operator('render.playblast', icon= 'FILE_MOVIE')

classes = (
    DUBLAST_settings,
    DUBLAST_PT_playblast_settings,
    DUBLAST_OT_playblast,
)

addon_keymaps = []

def register():
    # register
    for cls in classes:
        bpy.utils.register_class(cls)

    # New playblast attribute in the scenes
    if not hasattr( bpy.types.Scene, 'playblast' ):
        bpy.types.Scene.playblast = bpy.props.PointerProperty( type=DUBLAST_settings )

    # menus
    bpy.types.VIEW3D_MT_view.append(menu_func)

    # keymaps
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Playblast', space_type='VIEW_3D')
        kmi = km.keymap_items.new('render.playblast', 'RET', 'PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))

def unregister():
    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # menu
    bpy.types.VIEW3D_MT_view.remove(menu_func)

    # keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # attributes
    del bpy.types.Scene.playblast

if __name__ == "__main__":
    register()

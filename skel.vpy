import vapoursynth as vs
import havsfunc as haf
import hysteria as hys
import functools as fun
from vapoursynth import core
#core = vs.get_core() # deprecated method

def postprocess(n, f, clip, deinterlaced):
	if f.props['_Combed'] > 0:
		return deinterlaced
	else:
		return clip

# Index and load Matroska container (What MakeMKV decrypts to)
video = core.lsmas.LWLibavSource(source = r"D:\Users\jonat\Tmp\Working Folder\transcode\tvshows\_tmp_in\downtonabbeys1d1_title_t00_partone.mkv")

# Index and load VOB container (This may be what AnyDVD decrypts to)
# video = core.d2v.Source(input, threads, nocrop, rff)

# Force color matrix for standard definition video (DVD rips)
video = core.resize.Point(video, matrix_in_s = "170m")

# Force color matrix for high definition video (Blu-ray rips)
# video = core.resize.Point(video, matrix_in_s = "709")

# Remove dot-crawl and rainbowing (Optional)
# Visual flaws that are often seen together, a result of how analog footage (VHS) was handled before being captured digitally.
# Recommended to do this step before deinterlacing.
# Note: Bifrost works best if you are able to determine if the rainbowing were added before or after the video was telecined!  Please refer to the documentation for details on how to determine which it is.
# video = core.tcomb.TComb(video, mode = 2)
# video = core.bifrost.Bifrost(video, interlaced = True)

# Deinterlace video while maintaining duration.
# If you double rate deinterlace it to 59.94, then step through frame by frame , look at the pattern during a scene with motion (such as a camera pan).
# 1) If there is motion every frame, then it's interlaced content (and you would want to use 59.94p when deinterlacing).
# 2) If you get duplicates , then it's 29.97p content (then should not deinterlace - you want to field match to 29.97p).
# 3) If you get 3:2 pattern of repeats, then it's 23.976p content (then you should not deinterlace - it needs to be IVTC'ed).
# There are exceptions, and weird cadences, changing patterns, but those 3 should cover the majority of common scenarios.

# Deinterlace Method #1: VIVTC (Normal Deinterlace)

#video = core.vivtc.VFM(video, order = 1, cthresh = 9)
#matched_video		= core.vivtc.VFM(clip = video, order = 0, field = 0, mode = 0)
#deinterlaced_video	= core.eedi3.eedi3(matched_video, field = 0)
#postprocessed_video	= core.std.FrameEval(matched_video, fun.partial(postprocess, clip=matched_video, deinterlaced=deinterlaced_video), prop_src=matched_video)
#decimated_video		= core.vivtc.VDecimate(postprocessed_video, cycle = 6)
#video				= decimated_video

# Deinterlace Method #2: QTGMC (Double-rate Deinterlace)
# Note: QTGMC can output video at single or double-frame rate. (Special case where this may not work are BBC DVDs made for the US, which QTGMC will attempt to deinterlace to 24p when really it should be 25p.)
# Examples:
#   QTGMC( Preset="Slower", FPSDivisor=2, ShutterBlur=1, ShutterAngleSrc=30,  ShutterAngleOut=180 ) # Smooth single-rate output, when input has little blur
#   QTGMC( Preset="Slower", FPSDivisor=2, ShutterBlur=1, ShutterAngleSrc=180, ShutterAngleOut=180 ) # Keep "film" look on single-rate output, "film" input
#   QTGMC( Preset="Slower", FPSDivisor=2, ShutterBlur=2, ShutterAngleSrc=180, ShutterAngleOut=180, SBlurLimit=8 ) # Same but srongly reduce blur "bleeding"
#   QTGMC( Preset="Slower", FPSDivisor=1, ShutterBlur=1, ShutterAngleSrc=0,   ShutterAngleOut=720 ) # Blur some high shutter-speed footage, keep double rate
#video = haf.QTGMC(video, TFF = True) # Top field first
#video = haf.QTGMC(video, TFF = False) # Bottom field first
video = haf.QTGMC(video, Preset = "Slower", TFF = False, FPSDivisor = 2, ShutterBlur = 2, ShutterAngleSrc = 180, ShutterAngleOut = 180, SBlurLimit = 8) # Single-rate, reduce bleed

# Edge Case: Decimate PAL > NTSC DVD video
# Note: Won't work if PAL footage was made using hybrid video - not all of it will be telecined with the same pattern, and so won't decimate well with the same cycle setting, which must be applied to the entire clip.
# decimated_video	= core.vivtc.VDecimate(video, cycle = 6)
# video				= decimated_video

# Fix leftover combing artifacts if interlaced footage was improperly transfered (Optional)
# https://www.l33tmeatwad.com/vapoursynth101/using-filters-functions
# video = haf.daa(video)

# Apply spatio-temporal denoiser (Optional)
# https://www.l33tmeatwad.com/vapoursynth101/using-filters-functions
# Note: THIS BLURS THE VIDEO AND DESTROYS DETAIL IN BACKGROUND PAINTINGS FOR ANIMATION, USE WITH EXTREME CAUTION.

# Reduce banding (Best for digital sources since they lack film grain, especially useful for animated content with flat gradients).
# Test if your source needs debanding by performing a visual inspection with the video IN MOTION, never paused.
# Note: For best results use Flash3kyuu Deband after any smoothing (denoising) filters but before using any sharpening filters.
# Advanced usage:
# https://github.com/SAPikachu/flash3kyuu_deband/blob/master/docs/source/usage.rst
# video = core.f3kdb.Deband(video)

# Sharpen edges and outlines to compensate for bluriness introduced by filters (Best for 2d animated content)
# Note: If you need to apply other filters to a video it is always best to apply sharpening last in your filter chain to avoid preventing details that need to be filtered out from being sharpened and surviving the filter chain.  It also helps to insure the final output is sharp and not blurry as a result of the other filters applied to the source.
# video = hys.Hysteria(video)

# todo do you need to worry about fps so that audio will still match when remuxing?

# todo plug in rest of skeleton script and get some aspect ratio correction snippets... this whole thing is basically composed of snippets, mebbe you can simplify things by categorizing them into types of snippets for this workflow (source snippet, color matrix snippet, AR snippet, etc)

# Crop and resize to correct aspect ratio (Cropping optional)
# Neither NTSC nor PAL DVDs have a 1:1 PAR, and both can be squeezed to either Fullscreen 4:3 or stretched to Widescreen 16:9.
# Note: When cropping footage that has YUV color space, you will need to crop in multiples of 2.
# Use an AR calculator to crop while maintaining AR, to avoid distortion when resizing:
# https://andrew.hedges.name/experiments/aspect_ratio/
video = core.std.CropRel(video, left=2, top=2, right=0, bottom=0)
# video = video.resize.Spline36(640, 480) # DVD (NTSC) Fullscreen 4:3 640x480
video = video.resize.Spline36(856, 480) # DVD (NTSC) Widescreen 16:9 853.33[848|856]x480

# Temporarily display video info.
# This filter is invoked after the main filter chain so the text itself doesn't get filtered!
# Note: comment this line before encoding!
#video = video.text.ClipInfo()

# Note: Many filters do not support all color space types, so you may need to convert to a specific color space before using a particular function.

video.set_output()

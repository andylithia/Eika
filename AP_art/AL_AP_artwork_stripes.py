# Converting a given image file to GDS
# Dependencies: numpy, gdspy, PIL
# May 8 2022 - AL AnalogMiko.com 

import gdspy
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


# Define AP Layer Data Type
ld_AP = {"layer":74, "datatype": 0}
# Define AP Layer Minimal DRC Requirements
DRC_WIDTH = 3;
DRC_GAP   = 2;
# Loading Base Library
lib = gdspy.GdsLibrary(infile='AL_AP_artwork_test.gds', unit = 1e-9)
cell = lib.cells['AL_AP_artwork_test']

imgname = input("Enter image prefix: ")
target_w = int(input("Enter target width (µm): "))

k = Image.open(imgname+'.png').convert('L')
ksize = k.size
k_target_h = target_w/5; # Unit is 5 um, Physical Size: 425 um
k_scaling  = k_target_h/ksize[0]
ksize1 = np.dot(ksize,k_scaling).astype(int)
ksize2 = [ksize1[0],    ksize1[1]*10]
ksize3 = [ksize1[0]*10, ksize1[1]*10]
kr = k.resize(ksize2)
kr = kr.resize(ksize3,Image.NEAREST)
ka1 = (np.array(kr)>128).transpose()
kd = np.zeros(ksize2);
boundary_output = [];

# KA1 UNIT: 0.5um
for i in range(ksize3[0]):
    if((i%10)==0):
        iq = int(i/10); 
        # GAP FILLING
        # The problem with this approach is that the gap tend to get shifted to one direction
        # Consider a sliding-window approach if that's causing trouble
        #
        # Unit: 0.5um
        # DRC Rule requires that AP gap must > 2um    
        gap_counter = 4
        gap_pol     = ka1[iq*10][0]
        if(gap_pol):
            y0 = 0
        for j in range(ksize3[1]):
            pixel = ka1[iq*10][j]
            if(pixel):
                if(gap_pol):
                    kd[iq][j]   = 255
                    gap_counter = gap_counter + 1
                else:
                    if((gap_counter>=DRC_GAP*2)):
                        kd[iq][j]   = 255
                        gap_counter = 0
                        gap_pol     = 1
                        y0 = j;
                    else:
                        kd[iq][j]   = 0
                        gap_counter = gap_counter + 1
            else :
                if(gap_pol):
                    if((gap_counter>=DRC_WIDTH*2)):
                        kd[iq][j]   = 0
                        gap_counter = 0
                        gap_pol     = 0
                        y1 = j;
                        boundary_output.append((iq*5*1000,(iq*5+DRC_WIDTH)*1000, y0*500,y1*500)) # Unit: nm
                    else:
                        kd[iq][j]   = 255
                        gap_counter = gap_counter + 1
                else:
                    kd[iq][j]   = 0
                    gap_counter = gap_counter + 1
    if((i%10)>=DRC_WIDTH*2):
        ka1[i] = 0
        
ka1 = ka1.transpose()

kd_pil = np.array(Image.fromarray(np.uint8(kd.transpose())).resize(ksize3, Image.NEAREST)).transpose()
for i in range(ksize3[0]):
    if((i%10)>=DRC_WIDTH*2):
        kd_pil[i] = 0
kd_pil = kd_pil.transpose()
plt.imsave(imgname+'_conv.png',kd_pil);

# Writing GDS File
print('Writing',len(boundary_output),'Objects')
for sq in boundary_output:
    # gdspy doesn't seem to care about the system unit. Converting to um
    rect = gdspy.Rectangle((sq[0]/1000.0,1000-sq[2]/1000.0),(sq[1]/1000.0,1000-sq[3]/1000.0),**ld_AP)
    cell.add(rect)
cell.write_svg(imgname+'_GDS.svg')
lib.write_gds('AL_AP_artwork_output.gds')

# Exit
print("Done")

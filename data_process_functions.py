
import numpy as np
import torch,os,csv
from matplotlib import pyplot as plt

def reference_image_points(image_size, density=2):
    """
    :param image_size: (x, y), used for defining default grid image_points
    :param density: (x, y), point sample density in each of x and y, default n=2
    """
    if isinstance(density,int):
        density=(density,density)

    image_points = torch.flip(torch.cartesian_prod(
        torch.linspace(1, image_size[0], density[0]),
        torch.linspace(1, image_size[1] , density[1])
    ).t(),[0])
    
    image_points = torch.cat([
        image_points, 
        torch.zeros(1,image_points.shape[1])*image_size[0]/2,
        torch.ones(1,image_points.shape[1])
        ], axis=0)
    
    return image_points

def transform_t2t(tforms, tforms_inv,pairs):
    
    tforms_world_to_tool0 = tforms_inv[pairs[:,0],:,:]
    tforms_tool1_to_world = tforms[pairs[:,1],:,:]
    return torch.matmul(tforms_world_to_tool0, tforms_tool1_to_world)  # tform_tool1_to_tool0

def data_pairs_adjacent(num_frames):
    # obtain the data_pairs to compute the tarnsfomration between frames and the reference (first) frame
    
    return torch.tensor([[0,n0] for n0 in range(num_frames)])

def read_calib_matrices(filename_calib):
    # T{image->tool} = T{image_mm -> tool} * T{image_pix -> image_mm}}
    tform_calib = np.empty((8,4), np.float32)
    with open(filename_calib,'r') as csv_file:
        txt = [i.strip('\n').split(',') for i in csv_file.readlines()]
        tform_calib[0:4,:]=np.array(txt[1:5]).astype(np.float32)
        tform_calib[4:8,:]=np.array(txt[6:10]).astype(np.float32)
    return torch.tensor(tform_calib[0:4,:]),torch.tensor(tform_calib[4:8,:]), torch.tensor(tform_calib[4:8,:] @ tform_calib[0:4,:])

def plot_scan(gt,frame,saved_name,step,width = 4, scatter = 8, legend_size=50):


    fig = plt.figure(figsize=(35,15))
    axs=[]
    for i in range(2):
        axs.append(fig.add_subplot(1,2,i+1,projection='3d'))
    plt.tight_layout()
    
    # plot surface
    ysize, xsize = frame.shape[-2:]
    grid=np.meshgrid(np.linspace(0,1,ysize),np.linspace(0,1,xsize),indexing='ij')
    coord = np.zeros((3,ysize,xsize))

    for i_frame in range(0,gt.shape[0],step): 
        gx, gy, gz = [gt[i_frame, ii, :] for ii in range(3)]
        gx, gy, gz = gx.reshape(2, 2), gy.reshape(2, 2), gz.reshape(2, 2)
        coord[0]=gx[0,0]+(gx[1,0]-gx[0,0])*(grid[0])+(gx[0,1]-gx[0,0])*(grid[1])
        coord[1]=gy[0,0]+(gy[1,0]-gy[0,0])*(grid[0])+(gy[0,1]-gy[0,0])*(grid[1])
        coord[2]=gz[0,0]+(gz[1,0]-gz[0,0])*(grid[0])+(gz[0,1]-gz[0,0])*(grid[1])
         
        pix_intensities = (frame[i_frame, ...]/frame[i_frame, ...].max())
        for i,ax in enumerate(axs):
            ax.plot_surface(coord[0], coord[1], coord[2], facecolors=plt.cm.gray(pix_intensities), shade=False,linewidth=0, antialiased=True, alpha=0.5)
    # plot gt
    gx_all, gy_all, gz_all = [gt[:, ii, :] for ii in range(3)]
    for i,ax in enumerate(axs):
        ax.scatter(gx_all[...,0], gy_all[...,0], gz_all[...,0],  alpha=0.5, c = 'b', s=scatter)
        ax.scatter(gx_all[...,1], gy_all[...,1], gz_all[...,1],  alpha=0.5,c = 'r', s=scatter)
        ax.scatter(gx_all[...,2], gy_all[...,2], gz_all[...,2],  alpha=0.5, c = 'g',s=scatter)
        ax.scatter(gx_all[...,3], gy_all[...,3], gz_all[...,3],  alpha=0.5,c = 'k', s=scatter)
        # plot the first frame and the last frame
        plt.plot(gt[0,0,0:2], gt[0,1,0:2], gt[0,2,0:2], 'b', linewidth = width)
        plt.plot(gt[0,0,[1,3]], gt[0,1,[1,3]], gt[0,2,[1,3]], 'b', linewidth = width) 
        plt.plot(gt[0,0,[3,2]], gt[0,1,[3,2]], gt[0,2,[3,2]], 'b', linewidth = width) 
        plt.plot(gt[0,0,[2,0]], gt[0,1,[2,0]], gt[0,2,[2,0]], 'b', linewidth = width)
        plt.plot(gt[-1,0,0:2], gt[-1,1,0:2], gt[-1,2,0:2], 'r', linewidth = width)
        plt.plot(gt[-1,0,[1,3]], gt[-1,1,[1,3]], gt[-1,2,[1,3]], 'r', linewidth = width) 
        plt.plot(gt[-1,0,[3,2]], gt[-1,1,[3,2]], gt[-1,2,[3,2]], 'r', linewidth = width) 
        plt.plot(gt[-1,0,[2,0]], gt[-1,1,[2,0]], gt[-1,2,[2,0]], 'r', linewidth = width)


        ax.axis('equal')
        ax.grid(False)
        # ax.axis('off')
        ax.set_xlabel('x',fontsize=legend_size)
        ax.set_ylabel('y',fontsize=legend_size)
        ax.set_zlabel('z',fontsize=legend_size)
        plt.rc('xtick', labelsize=legend_size)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=legend_size)    # fontsize of the tick labels
        if i==0:
            ax.view_init(10,30,0)
        else:
            ax.view_init(30,30,0)


    plt.savefig(saved_name +'.png')
    plt.close()

                
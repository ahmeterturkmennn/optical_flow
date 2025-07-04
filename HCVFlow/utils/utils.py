import torch
import torch.nn.functional as F
import numpy as np
from scipy import interpolate
import cv2

class InputPadder:
    """ Pads images such that dimensions are divisible by 8 """

    def __init__(self, dims, mode='sintel', padding_factor=8):
        self.ht, self.wd = dims[-2:]
        pad_ht = (((self.ht // padding_factor) + 1) * padding_factor - self.ht) % padding_factor
        pad_wd = (((self.wd // padding_factor) + 1) * padding_factor - self.wd) % padding_factor
        if mode == 'sintel':
            self._pad = [pad_wd // 2, pad_wd - pad_wd // 2, pad_ht // 2, pad_ht - pad_ht // 2]
        else:
            self._pad = [pad_wd // 2, pad_wd - pad_wd // 2, 0, pad_ht]

    def pad(self, *inputs):
        return [F.pad(x, self._pad, mode='replicate') for x in inputs]

    def unpad(self, x):
        ht, wd = x.shape[-2:]
        c = [self._pad[2], ht - self._pad[3], self._pad[0], wd - self._pad[1]]
        return x[..., c[0]:c[1], c[2]:c[3]]


def forward_interpolate(flow):
    flow = flow.detach().cpu().numpy()  # [2, H, W]
    dx, dy = flow[0], flow[1]

    ht, wd = dx.shape
    x0, y0 = np.meshgrid(np.arange(wd), np.arange(ht))

    x1 = x0 + dx
    y1 = y0 + dy

    x1 = x1.reshape(-1)
    y1 = y1.reshape(-1)
    dx = dx.reshape(-1)
    dy = dy.reshape(-1)

    valid = (x1 > 0) & (x1 < wd) & (y1 > 0) & (y1 < ht)
    x1 = x1[valid]
    y1 = y1[valid]
    dx = dx[valid]
    dy = dy[valid]

    flow_x = interpolate.griddata(
        (x1, y1), dx, (x0, y0), method='nearest', fill_value=0)

    flow_y = interpolate.griddata(
        (x1, y1), dy, (x0, y0), method='nearest', fill_value=0)

    flow = np.stack([flow_x, flow_y], axis=0)
    return torch.from_numpy(flow).float()


# def bilinear_sampler(img, coords, mode='bilinear', mask=False):
#     """ Wrapper for grid_sample, uses pixel coordinates """
#     if coords.size(-1) != 2:  # [B, 2, H, W] -> [B, H, W, 2]
#         coords = coords.permute(0, 2, 3, 1)

#     H, W = img.shape[-2:]
#     # H = height if height is not None else img.shape[-2]
#     # W = width if width is not None else img.shape[-1]

#     xgrid, ygrid = coords.split([1, 1], dim=-1)

#     # To handle H or W equals to 1 by explicitly defining height and width
#     if H == 1:
#         assert ygrid.abs().max() < 1e-8
#         H = 10
#     if W == 1:
#         assert xgrid.abs().max() < 1e-8
#         W = 10

#     xgrid = 2 * xgrid / (W - 1) - 1
#     ygrid = 2 * ygrid / (H - 1) - 1

#     grid = torch.cat([xgrid, ygrid], dim=-1)
#     img = F.grid_sample(img, grid, mode=mode, align_corners=True)

#     if mask:
#         mask = (xgrid > -1) & (ygrid > -1) & (xgrid < 1) & (ygrid < 1)
#         return img, mask.squeeze(-1).float()

#     return img

def bilinear_sampler(img, coords, mode='bilinear', mask=False):
    """ Wrapper for grid_sample, uses pixel coordinates """
    H, W = img.shape[-2:]
    xgrid, ygrid = coords.split([1,1], dim=-1)
    xgrid = 2*xgrid/(W-1) - 1
    ygrid = 2*ygrid/(H-1) - 1

    grid = torch.cat([xgrid, ygrid], dim=-1)
    img = F.grid_sample(img, grid, align_corners=True)

    if mask:
        mask = (xgrid > -1) & (ygrid > -1) & (xgrid < 1) & (ygrid < 1)
        return img, mask.float()

    return img

def bilinear_sampler_1d(img, coords, mode='bilinear', mask=False):
    """ Wrapper for grid_sample, uses pixel coordinates """
    H, W = img.shape[-2:]
    xgrid, ygrid = coords.split([1,1], dim=-1)
    xgrid = 2*xgrid/(W-1) - 1
    assert torch.unique(ygrid).numel() == 1 and H == 1 # This is a stereo problem

    grid = torch.cat([xgrid, ygrid], dim=-1)
    img = F.grid_sample(img, grid, align_corners=True)
    if mask:
        mask = (xgrid > -1) & (ygrid > -1) & (xgrid < 1) & (ygrid < 1)
        return img, mask.float()
    return img


def coords_grid(batch, ht, wd, normalize=False):
    if normalize:  # [-1, 1]
        coords = torch.meshgrid(2 * torch.arange(ht) / (ht - 1) - 1,
                                2 * torch.arange(wd) / (wd - 1) - 1)
    else:
        coords = torch.meshgrid(torch.arange(ht), torch.arange(wd))
    coords = torch.stack(coords[::-1], dim=0).float()
    return coords[None].repeat(batch, 1, 1, 1)  # [B, 2, H, W]


def coords_grid_np(h, w):  # used for accumulating high speed sintel flow data
    coords = np.meshgrid(np.arange(h, dtype=np.float32),
                         np.arange(w, dtype=np.float32), indexing='ij')
    coords = np.stack(coords[::-1], axis=-1)  # [H, W, 2]

    return coords


def normalize_coords(grid):
    """Normalize coordinates of image scale to [-1, 1]
    Args:
        grid: [B, 2, H, W]
    """
    assert grid.size(1) == 2
    h, w = grid.size()[2:]
    grid[:, 0, :, :] = 2 * (grid[:, 0, :, :].clone() / (w - 1)) - 1  # x: [-1, 1]
    grid[:, 1, :, :] = 2 * (grid[:, 1, :, :].clone() / (h - 1)) - 1  # y: [-1, 1]
    # grid = grid.permute((0, 2, 3, 1))  # [B, H, W, 2]
    return grid


def flow_warp(feature, flow, mask=False):
    b, c, h, w = feature.size()
    assert flow.size(1) == 2

    grid = coords_grid(b, h, w).to(flow.device) + flow  # [B, 2, H, W]

    return bilinear_sampler(feature, grid, mask=mask)


def upflow8(flow, mode='bilinear'):
    new_size = (8 * flow.shape[2], 8 * flow.shape[3])
    return 8 * F.interpolate(flow, size=new_size, mode=mode, align_corners=True)


def bilinear_upflow(flow, scale_factor=8):
    assert flow.size(1) == 2
    flow = F.interpolate(flow, scale_factor=scale_factor,
                         mode='bilinear', align_corners=True) * scale_factor

    return flow


def upsample_flow(flow, img):
    if flow.size(-1) != img.size(-1):
        scale_factor = img.size(-1) / flow.size(-1)
        flow = F.interpolate(flow, size=img.size()[-2:],
                             mode='bilinear', align_corners=True) * scale_factor
    return flow


def count_parameters(model):
    num = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return num


def set_bn_eval(m):
    classname = m.__class__.__name__
    if classname.find('BatchNorm') != -1:
        m.eval()
def _make_color_wheel():
    ry, yg, gc, cb, bm, mr = 15, 6, 4, 11, 13, 6
    ncols = ry + yg + gc + cb + bm + mr
    colorwheel = np.zeros([ncols, 3])
    col = 0
    # R‑Y
    colorwheel[0:ry, 0] = 255
    colorwheel[0:ry, 1] = np.floor(255*np.arange(0, ry)/ry)
    col += ry
    # Y‑G
    colorwheel[col:col+yg, 0] = 255 - np.floor(255*np.arange(0, yg)/yg)
    colorwheel[col:col+yg, 1] = 255
    col += yg
    # G‑C
    colorwheel[col:col+gc, 1] = 255
    colorwheel[col:col+gc, 2] = np.floor(255*np.arange(0, gc)/gc)
    col += gc
    # C‑B
    colorwheel[col:col+cb, 1] = 255 - np.floor(255*np.arange(0, cb)/cb)
    colorwheel[col:col+cb, 2] = 255
    col += cb
    # B‑M
    colorwheel[col:col+bm, 2] = 255
    colorwheel[col:col+bm, 0] = np.floor(255*np.arange(0, bm)/bm)
    col += bm
    # M‑R
    colorwheel[col:col+mr, 2] = 255 - np.floor(255*np.arange(0, mr)/mr)
    colorwheel[col:col+mr, 0] = 255
    return colorwheel


def flow_to_image(flow, clip_flow=None):
    u = flow[..., 0]
    v = flow[..., 1]

    if clip_flow is not None:
        u = np.clip(u, -clip_flow, clip_flow)
        v = np.clip(v, -clip_flow, clip_flow)

    rad = np.sqrt(u**2 + v**2)
    ang = np.arctan2(-v, -u) / np.pi

    ncols = 55
    colorwheel = _make_color_wheel()
    fk = (ang + 1) / 2 * (ncols - 1)  # [-1,1] → [0,ncols)
    k0 = np.floor(fk).astype(int)
    k1 = (k0 + 1) % ncols
    f  = fk - k0

    img = np.zeros((flow.shape[0], flow.shape[1], 3), dtype=np.uint8)

    for i in range(3):
        col0 = colorwheel[k0, i] / 255.0
        col1 = colorwheel[k1, i] / 255.0
        col  = (1 - f) * col0 + f * col1

        # adjust saturation by flow magnitude
        col[rad <= 1]  = 1 - rad[rad <= 1] * (1 - col[rad <= 1])
        col[rad >  1] *= 0.75  # out‑of‑range ⇒ desaturate

        img[..., i] = np.floor(255 * col)

    return img
import torch
import torch.nn as nn

class SingleCenterLoss(nn.Module):
    """
    Single Center Loss
    
    Reference:
    J Li, Frequency-aware Discriminative Feature Learning Supervised by Single-CenterLoss for Face Forgery Detection, CVPR 2021.
    
    Parameters:
        m (float): margin parameter. 
        D (int): feature dimension.
        C (vector): learnable center.
    """
    def __init__(self, m = 0.01, D = 192, use_gpu=True):
        super(SingleCenterLoss, self).__init__()
        self.m = m
        self.D = D
        self.margin = self.m * torch.sqrt(torch.tensor(self.D).float())
        self.use_gpu = use_gpu
        self.l2loss = nn.MSELoss(reduction = 'none')

        if self.use_gpu:
            self.C = nn.Parameter(torch.randn(self.D).to('cuda:0'))
        else:
            self.C = nn.Parameter(torch.randn(self.D))

    def forward(self, x, labels):
        """
        Args:
            x: feature matrix with shape (batch_size, feat_dim).
            labels: ground truth labels with shape (batch_size).
        """
        batch_size = x.size(0)
        eud_mat = torch.sqrt(self.l2loss(x, self.C.expand(batch_size, self.C.size(0))).sum(dim=1, keepdim=True))

        labels = labels.unsqueeze(1)

        real_count = (1-labels).sum()
        
        dist_real = (eud_mat * (1-labels.float())).clamp(min=1e-12, max=1e+12).sum()
        dist_fake = (eud_mat * labels.float()).clamp(min=1e-12, max=1e+12).sum()

        if real_count != 0:
            dist_real /= real_count

        if real_count != batch_size:
            dist_fake /= (batch_size - real_count)
        # print(dist_real, dist_fake)
        max_margin = dist_real - dist_fake + self.margin

        if max_margin < 0:
            max_margin = 0

        loss = dist_real + max_margin

        return loss
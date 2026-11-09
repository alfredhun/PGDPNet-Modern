import torch
from torch import nn

def sigmoid_focal_loss_cpu(logits, targets, gamma, alpha):
    num_classes = logits.shape[1]
    gamma = gamma[0] if isinstance(gamma, (list, tuple, torch.Tensor)) else gamma
    alpha = alpha[0] if isinstance(alpha, (list, tuple, torch.Tensor)) else alpha
    dtype = targets.dtype
    device = targets.device
    class_range = torch.arange(1, num_classes+1, dtype=dtype, device=device).unsqueeze(0)

    t = targets.unsqueeze(1)
    p = torch.sigmoid(logits)
    term1 = (1 - p) ** gamma * torch.log(p.clamp(min=1e-12))
    term2 = p ** gamma * torch.log((1 - p).clamp(min=1e-12))
    return -torch.where(t == class_range, alpha * term1, (1 - alpha) * term2)

class SigmoidFocalLoss(nn.Module):
    def __init__(self, gamma, alpha):
        super(SigmoidFocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits, targets):
        return sigmoid_focal_loss_cpu(logits, targets, self.gamma, self.alpha)

    def __repr__(self):
        tmpstr = self.__class__.__name__ + "("
        tmpstr += "gamma=" + str(self.gamma)
        tmpstr += ", alpha=" + str(self.alpha)
        tmpstr += ")"
        return tmpstr


class BCEFocalLoss(nn.Module):
    def __init__(self, gamma=2, alpha=0.25, reduction='mean'):
        super(BCEFocalLoss, self).__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction

    def forward(self, predict, target):
        pt = torch.sigmoid(predict)
        loss = - self.alpha * (1 - pt) ** self.gamma * target * torch.log(pt.clamp(min=1e-12)) - \
               (1 - self.alpha) * pt ** self.gamma * (1 - target) * torch.log((1 - pt).clamp(min=1e-12))
        if self.reduction == 'mean':
            return torch.mean(loss)
        elif self.reduction == 'sum':
            return torch.sum(loss)
        return loss

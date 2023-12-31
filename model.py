import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import numpy as np

class SimpleObjectDetectorWithBackbone(nn.Module):
    def __init__(self, num_boxes=10, num_classes=38, pretrained=True):
        super(SimpleObjectDetectorWithBackbone, self).__init__()
        self.num_boxes = num_boxes
        self.num_classes = num_classes

        # Load a pretrained MobileNet model
        mobilenet = models.mobilenet_v2(pretrained = pretrained)
        self.backbone = mobilenet.features

        # Adjust this based on the output size of your backbone
        fc_1_features = 243200  # Adjust for the output size of MobileNet
        #fc_2_features = 2304

        # Fully connected layers
        self.fc1 = nn.Linear(fc_1_features, 256)
        #self.fc2 = nn.Linear(fc_2_features, 256)
        self.det_head = nn.Linear(256, num_boxes * 5)  # Detection head
        self.cls_head = nn.Linear(256, num_boxes * num_classes)  # Classification head
        self.conf_head = nn.Linear(256, num_boxes)  # Confidence head

    def forward(self, x):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        #x = F.relu(self.fc2(x))
        #print(torch.sigmoid(self.det_head(x).view(-1, self.num_boxes, 5)))
        detection = torch.sigmoid(self.det_head(x).view(-1, self.num_boxes, 5)) *2* np.pi
        classification = self.cls_head(x).view(-1, self.num_boxes, self.num_classes)
        confidence = torch.sigmoid(self.conf_head(x)).view(-1, self.num_boxes, 1)
        return detection, classification, confidence

#original res
class SimpleObjectDetector(nn.Module):
    def __init__(self, num_boxes=5, num_classes=38):
        super(SimpleObjectDetector, self).__init__()
        self.num_boxes = num_boxes
        self.num_classes = num_classes

        # Original convolutional layers
        self.conv1 = nn.Conv2d(3, 8, kernel_size=3, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(8)
        self.conv2 = nn.Conv2d(8, 16, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(16)
        self.conv3 = nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(32)

        # Additional convolutional layers
        self.conv4 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(64)
        self.conv5 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn5 = nn.BatchNorm2d(128)
        self.conv6 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn6 = nn.BatchNorm2d(256)
        #self.conv7 = nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1)
        #self.bn7 = nn.BatchNorm2d(512)


        # Pooling layer
        self.pool = nn.MaxPool2d(2, 2)

        # Calculate the flattened size after convolution and pooling layers
        # Assuming the input image size is 1920x960
        # The size after conv and pool layers would still be [32, 120, 60]
        fc_1_features = 4608
        fc_2_features = 2304

        self.dropout1 = nn.Dropout(0.1)
        self.dropout2 = nn.Dropout(0.1)

        # Fully connected layers
        self.fc1 = nn.Linear(fc_1_features, fc_2_features)
        self.fc2 = nn.Linear(fc_2_features, 256)
        self.det_head = nn.Linear(256, num_boxes * 5)  # Detection head
        self.cls_head = nn.Linear(256, num_boxes * num_classes)  # Classification head
        self.conf_head = nn.Linear(256, num_boxes)  # Confidence head

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.pool(self.bn3(F.relu(self.conv3(x))))
        x = self.pool((F.relu(self.conv4(x))))
        x = self.pool((F.relu(self.conv5(x))))
        #x = F.relu(self.bn6(self.conv6(x)))
        #x = F.relu(self.bn7(self.conv7(x)))
        #x = self.pool(x)

        # Flatten the features for the fully connected layer
        x = x.view(x.size(0), -1)
        print(x.size())
        x = self.dropout1(F.relu(self.fc1(x)))
        x = self.dropout2(F.relu(self.fc2(x)))

        # Apply detection, classification, and confidence heads
        detection = torch.sigmoid(self.det_head(x).view(-1, self.num_boxes, 5)) *2* np.pi
        classification = self.cls_head(x).view(-1, self.num_boxes, self.num_classes)
        confidence = torch.sigmoid(self.conf_head(x)).view(-1, self.num_boxes, 1)

        return detection, classification, confidence
# Implementation of this model is borrowed and modified
# (from torch to paddle) from here:
# https://github.com/black0017/MedicalZooPytorch

# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))

import paddle
import paddle.nn as nn


from medicalseg.cvlibs import manager
class EncoderBlock(nn.Layer):
    def __init__(
        self,
        name_scope,
        in_channels=None,
        kernel_number=8,
        downsample=True,
        norm=True,
        kernel_size=3,
        dropout=0.6,
    ):
        super(EncoderBlock, self).__init__(name_scope=name_scope)
        self.norm = norm
        if in_channels is None:
            in_channels = kernel_number // 2

        self.lrelu = nn.LeakyReLU()
        self.dropout = nn.Dropout3D(p=dropout)

        if norm:
            self.norm1 = nn.InstanceNorm3D(kernel_number)
            self.norm2 = nn.InstanceNorm3D(kernel_number)
        self.norm3 = nn.InstanceNorm3D(kernel_number)

        self.conv1 = nn.Conv3D(
            in_channels=in_channels,
            out_channels=kernel_number,
            kernel_size=kernel_size,
            stride=2 if downsample else 1,
            padding="SAME",
            bias_attr=False,
        )
        self.conv2 = nn.Conv3D(
            in_channels=kernel_number,
            out_channels=kernel_number,
            kernel_size=kernel_size,
            stride=1,
            padding="SAME",
            bias_attr=False,
        )
        self.conv3 = nn.Conv3D(
            in_channels=kernel_number,
            out_channels=kernel_number,
            kernel_size=kernel_size,
            stride=1,
            padding="SAME",
            bias_attr=False,
        )

    def forward(self, x):
        out = self.conv1(x)
        residual = out
        if self.norm:
            out = self.norm1(out)
        out = self.lrelu(out)
        out = self.conv2(out)
        out = self.dropout(out)
        if self.norm:
            out = self.norm2(out)
        out = self.lrelu(out)
        out = self.conv3(out)
        out += residual
        out = self.norm3(out)
        out = self.lrelu(out)
        return out

class AttentionGate(nn.Layer):
    def __init__(self, kernel_number):
        super(AttentionGate, self).__init__()
        self.relu = nn.LeakyReLU()
        self.sigmoid = nn.Sigmoid()
        self.upsample = nn.Upsample(scale_factor=2, mode="trilinear", data_format="NCDHW")

        self.conv_skip = nn.Conv3D(
            in_channels=kernel_number,
            out_channels=kernel_number,
            kernel_size=2,
            stride=2,
            padding=0,
            bias_attr=False,
        )
        self.conv_dec = nn.Conv3D(
            in_channels=kernel_number * 2,
            out_channels=kernel_number,
            kernel_size=1,
            stride=1,
            padding=0,
            bias_attr=False,
        )
        self.conv_point = nn.Conv3D(
            in_channels=kernel_number,
            out_channels=1,
            kernel_size=1,
            stride=1,
            padding=0,
            bias_attr=False,
        )
        self.norm_skip = nn.BatchNorm3D(kernel_number)
        self.norm_dec = nn.BatchNorm3D(kernel_number)
        self.norm_alpha = nn.BatchNorm3D(1)

    def forward(self, skip, dec):
        skip_down = self.conv_skip(skip)
        skip_down = self.norm_skip(skip_down)

        dec = self.conv_dec(dec)
        dec = self.norm_dec(dec)

        out = skip_down + dec
        out = self.relu(out)

        out = self.conv_point(out)
        out = self.norm_alpha(out)
        out = self.upsample(out)
        out = self.sigmoid(out)

        return skip * out


class DecoderBlock(nn.Layer):
    def __init__(self, name_scope, kernel_number, num_classes, kernel_size=3, stride=1):
        super(DecoderBlock, self).__init__(name_scope=name_scope)
        self.dropout = nn.Dropout3D(p=0.6)
        self.lrelu = nn.LeakyReLU()
        self.ag = AttentionGate(kernel_number)

        self.upsample = nn.Upsample(scale_factor=2, mode="trilinear", data_format="NCDHW")
        self.conv1 = nn.Conv3D(
            in_channels=kernel_number * 3,
            out_channels=kernel_number * 2,
            kernel_size=kernel_size,
            stride=stride,
            padding="SAME",
            bias_attr=False,
        )
        self.norm1 = nn.InstanceNorm3D(kernel_number * 2)

        self.conv2 = nn.Conv3D(
            in_channels=kernel_number * 2,
            out_channels=kernel_number,
            kernel_size=kernel_size,
            stride=stride,
            padding="SAME",
            bias_attr=False,
        )
        self.norm2 = nn.InstanceNorm3D(kernel_number)

        self.conv3 = nn.Conv3D(
            in_channels=kernel_number,
            out_channels=kernel_number,
            kernel_size=kernel_size,
            stride=stride,
            padding="SAME",
            bias_attr=False,
        )

        self.shortcut_conv = nn.Conv3D(
            in_channels=kernel_number,
            out_channels=num_classes,
            kernel_size=1,
            stride=1,
            padding="SAME",
            # bias_attr=False,
        )

        self.norm3 = nn.InstanceNorm3D(kernel_number)

    def forward(self, x, skip):
        skip = self.ag(skip, x)

        out = self.upsample(x)

        out = paddle.concat([out, skip], axis=1)

        out = self.conv1(out)
        out = self.norm1(out)
        out = self.lrelu(out)

        out = self.conv2(out)
        out = self.norm2(out)
        out = self.lrelu(out)

        out = self.conv3(out)
        out = self.norm3(out)
        out = self.lrelu(out)
        shortcut = out

        shortcut = self.shortcut_conv(shortcut)
        return out, shortcut

@manager.MODELS.add_component
class UNetAtt(nn.Layer):
    """
    Implementations based on the Unet3D paper: https://arxiv.org/abs/1606.06650
    """

    def __init__(self, in_channels, num_classes, pretrained=None, base_n_kernel=8, dropout=0.3):
        super(UNetAtt, self).__init__()
        self.num_classes = num_classes
        self.best_loss = 1000000

        self.upsample = nn.Upsample(scale_factor=2, mode="trilinear", data_format="NCDHW")
        self.pad = nn.Pad3D([1, 0, 1, 0, 1, 0])
        self.padded = False

        self.encb1 = EncoderBlock(
            "encoder1", in_channels, base_n_kernel * 2**0, downsample=False, dropout=dropout
        )  # 8, orig
        self.encb2 = EncoderBlock("encoder2", kernel_number=base_n_kernel * 2**1, dropout=dropout)  # 16, orig/2
        self.encb3 = EncoderBlock("encoder3", kernel_number=base_n_kernel * 2**2, dropout=dropout)  # 32, orig/4
        self.encb4 = EncoderBlock("encoder4", kernel_number=base_n_kernel * 2**3, dropout=dropout)  # 64, orig/8

        self.encb5 = EncoderBlock(
            "encoder5", in_channels=base_n_kernel * 2**3, kernel_number=base_n_kernel * 2**4, dropout=dropout
        )  # 128, orig/16

        self.decb4 = DecoderBlock("decoder4", base_n_kernel * 2**3, num_classes)
        self.decb3 = DecoderBlock("decoder3", base_n_kernel * 2**2, num_classes)
        self.decb2 = DecoderBlock("decoder2", base_n_kernel * 2**1, num_classes)
        self.decb1 = DecoderBlock("decoder1", base_n_kernel * 2**0, num_classes)

        self.decconv = nn.Conv3D(
            in_channels=base_n_kernel, out_channels=num_classes, kernel_size=1, stride=1
        )

        self.outputconv = nn.Conv3D(
            in_channels=num_classes * 2, out_channels=num_classes, kernel_size=1, stride=1
        )

    def forward(self, x):
        if x.shape[2] % 2 != 0:
            x = self.pad(x)
            self.padded = True

        enc1 = self.encb1(x)
        enc2 = self.encb2(enc1)
        enc3 = self.encb3(enc2)
        enc4 = self.encb4(enc3)

        enc5 = self.encb5(enc4)

        out, ds4 = self.decb4(enc5, enc4)
        out, ds3 = self.decb3(enc4, enc3)
        out, ds2 = self.decb2(enc3, enc2)
        out, _ = self.decb1(enc2, enc1)

        out = self.decconv(out)

        # ds4_up = self.upsample(ds4)
        # ds3 += ds4_up
        ds3_up = self.upsample(ds3)
        ds2 += ds3_up
        ds2_up = self.upsample(ds2)
        out += ds2_up

        if self.padded:
            out = out[:, :, 1:, 1:, 1:]

        return [out]




# @manager.MODELS.add_component
# class UNetAtt(nn.Layer):
#     """
#     Implementations based on the Unet3D and attention Unet paper: https://arxiv.org/abs/1606.06650 https://arxiv.org/abs/1804.03999
#     """

#     def __init__(self, in_channels, num_classes, pretrained=None, base_n_kernel=8, dropout=0.3):
#         super(UNet, self).__init__()
#         self.num_classes = num_classes
#         self.best_loss = 1000000

#         self.upsample = nn.Upsample(scale_factor=2, mode="trilinear", data_format="NCDHW")
#         self.pad = nn.Pad3D([1, 0, 1, 0, 1, 0])
#         self.padded = False

#         self.encb1 = EncoderBlock(
#             "encoder1", in_channels, base_n_kernel * 2**0, downsample=False, dropout=dropout
#         )  # 8, orig
#         self.encb2 = EncoderBlock("encoder2", kernel_number=base_n_kernel * 2**1, dropout=dropout)  # 16, orig/2
#         self.encb3 = EncoderBlock("encoder3", kernel_number=base_n_kernel * 2**2, dropout=dropout)  # 32, orig/4
#         self.encb4 = EncoderBlock("encoder4", kernel_number=base_n_kernel * 2**3, dropout=dropout)  # 64, orig/8

#         self.encb5 = EncoderBlock(
#             "encoder5", in_channels=base_n_kernel * 2**3, kernel_number=base_n_kernel * 2**4, dropout=dropout
#         )  # 128, orig/16

#         self.decb4 = DecoderBlock("decoder4", base_n_kernel * 2**3, num_classes)
#         self.decb3 = DecoderBlock("decoder3", base_n_kernel * 2**2, num_classes)
#         self.decb2 = DecoderBlock("decoder2", base_n_kernel * 2**1, num_classes)
#         self.decb1 = DecoderBlock("decoder1", base_n_kernel * 2**0, num_classes)

#         self.decconv = nn.Conv3D(
#             in_channels=base_n_kernel, out_channels=num_classes, kernel_size=1, stride=1
#         )

#         self.outputconv = nn.Conv3D(
#             in_channels=num_classes * 2, out_channels=num_classes, kernel_size=1, stride=1
#         )

#     def forward(self, x):
#         if x.shape[2] % 2 != 0:
#             x = self.pad(x)
#             self.padded = True

#         enc1 = self.encb1(x)
#         enc2 = self.encb2(enc1)
#         enc3 = self.encb3(enc2)
#         enc4 = self.encb4(enc3)

#         enc5 = self.encb5(enc4)

#         out, ds4 = self.decb4(enc5, enc4)
#         out, ds3 = self.decb3(enc4, enc3)
#         out, ds2 = self.decb2(enc3, enc2)
#         out, _ = self.decb1(enc2, enc1)

#         out = self.decconv(out)

#         # ds4_up = self.upsample(ds4)
#         # ds3 += ds4_up
#         ds3_up = self.upsample(ds3)
#         ds2 += ds3_up
#         ds2_up = self.upsample(ds2)
#         out += ds2_up

#         if self.padded:
#             out = out[:, :, 1:, 1:, 1:]

#         return [out]


#     def forward(self, x):
#         if x.shape[2] % 2 != 0:
#             x = self.pad(x)
#             self.padded = True

#         enc1 = self.encb1(x)
#         # print("enc1", enc1.shape)
#         enc2 = self.encb2(enc1)
#         # print("enc2", enc2.shape)
#         enc3 = self.encb3(enc2)
#         # print("enc3", enc3.shape)
#         enc4 = self.encb4(enc3)
#         # print("enc4", enc4.shape)

#         enc5 = self.encb5(enc4)
#         # print("enc5", enc5.shape)

#         out, ds4 = self.decb4(enc5, enc4)
#         # print("dec4", out.shape)
#         out, ds3 = self.decb3(enc4, enc3)
#         # print("dec3", out.shape)
#         out, ds2 = self.decb2(enc3, enc2)
#         # print("dec2", out.shape)
#         out, _ = self.decb1(enc2, enc1)
#         # print("dec1", out.shape)

#         out = self.decconv(out)

#         ds4_up = self.upsample(ds4)
#         ds3 += ds4_up
#         ds3_up = self.upsample(ds3)
#         ds2 += ds3_up
#         ds2_up = self.upsample(ds2)
#         out = out + ds2_up

#         if self.padded:
#             out = out[:, :, 1:, 1:, 1:]

#         return [out]


if __name__ == "__main__":
    size = 64
    num_classes = 3
    input = paddle.static.InputSpec([None, 1, size, size, size], "float32", "x")
    label = paddle.static.InputSpec([None, num_classes, size, size, size], "int64", "label")

    unet_att = UNetAtt(in_channels=1, num_classes=3)

    paddle.Model(unet_att, input, label).summary()

    input = paddle.rand((2, 1, size, size, size))
    print("input", input.shape)

    output = unet_att(input)
    print("output", output[0].shape)

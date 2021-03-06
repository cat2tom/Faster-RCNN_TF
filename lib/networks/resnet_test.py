import tensorflow as tf
from networks.network import Network
from networks.resnet_train import resnet_base

#define

n_classes = 21
_feat_stride = [16,]
anchor_scales = [8, 16, 32]


class resnet_test(resnet_base):
    def __init__(self, trainable=True, n = 50):
        super(self.__class__, self).__init__()

        self.inputs = []
        self.data = tf.placeholder(tf.float32, shape=[None, None, None, 3])
        self.im_info = tf.placeholder(tf.float32, shape=[None, 3])
        self.keep_prob = tf.placeholder(tf.float32)
        self.layers = dict({'data':self.data, 'im_info':self.im_info})
        self.trainable = trainable
        self.setup()


    def setup(self):
        #
        (self.feed('data')
             #.conv(7, 7, 64, 2, 2, name='conv1', trainable=False, bn=True, relu=True)
             .conv(7, 7, 64, 2, 2, name='conv1', relu=False)
             .batch_normalization(relu=True, name='bn_conv1', is_training=False)
             .max_pool(3, 3, 2, 2, padding='VALID', name='pool1'))

        (self.residual_block('pool1', 'res2a', 64, 256, projection=True, trainable=False)
         .residual_block('res2a', 'res2b', 64, 256, projection=False, trainable=False)
         .residual_block('res2b', 'res2c', 64, 256, projection=False, trainable=False)
         .residual_block('res2c', 'res3a', 128, 512, projection=True, trainable=False, padding='VALID')
         .residual_block('res3a', 'res3b', 128, 512, projection=False, trainable=False)
         .residual_block('res3b', 'res3c', 128, 512, projection=False, trainable=False)
         .residual_block('res3c', 'res3d', 128, 512, projection=False, trainable=False)
         .residual_block('res3d', 'res4a', 256, 1024, projection=True, trainable=False, padding='VALID')
         .residual_block('res4a', 'res4b', 256, 1024, projection=False, trainable=False)
         .residual_block('res4b', 'res4c', 256, 1024, projection=False, trainable=False)
         .residual_block('res4c', 'res4d', 256, 1024, projection=False, trainable=False)
         .residual_block('res4d', 'res4e', 256, 1024, projection=False, trainable=False)
         .residual_block('res4e', 'res4f', 256, 1024, projection=False, trainable=False)
         )

        #========= RPN ============
        (self.feed('res4f_relu')
             .conv(3,3,512,1,1,name='rpn_conv/3x3',relu=True, bn=False)
             .conv(1,1,len(anchor_scales)*3*2 ,1 , 1, padding='VALID', relu = False, name='rpn_cls_score', bn=False))

        # Loss of rpn_cls & rpn_boxes

        (self.feed('rpn_conv/3x3')
             .conv(1,1,len(anchor_scales)*3*4, 1, 1, padding='VALID', relu = False, name='rpn_bbox_pred',bn=False))

        #========= RoI Proposal ============
        (self.feed('rpn_cls_score')
             .spatial_reshape_layer(2,name = 'rpn_cls_score_reshape')
             .spatial_softmax(name='rpn_cls_prob'))

        (self.feed('rpn_cls_prob')
             .spatial_reshape_layer(len(anchor_scales)*3*2,name = 'rpn_cls_prob_reshape'))

        (self.feed('rpn_cls_prob_reshape','rpn_bbox_pred','im_info')
             .proposal_layer(_feat_stride, anchor_scales, 'TEST',name = 'rois'))

        #========= RCNN ============
        (self.feed('res4f_relu', 'rois')
             .roi_pool(7, 7, 1.0/16, name='res5a_branch2a_roipooling')
         .residual_block('res5a_branch2a_roipooling', 'res5a', 512, 2048, projection=True, trainable=True, padding='VALID')
         .residual_block('res5a', 'res5b', 512, 2048, projection=False, trainable=True)
         .residual_block('res5b', 'res5c', 512, 2048, projection=False, trainable=True)
         .fc(n_classes, relu=False, name='cls_score')
         .softmax(name='cls_prob')
         )
        (self.feed('res5c_relu')
             .fc(n_classes*4, relu=False, name='bbox_pred'))
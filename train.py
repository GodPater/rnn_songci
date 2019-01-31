#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os

import tensorflow as tf

import utils
from model import Model
from utils import read_data

from flags import parse_args
FLAGS, unparsed = parse_args()


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', level=logging.DEBUG)


vocabulary = read_data(FLAGS.text)
print('Data size', len(vocabulary))
ckpt_steps = (len(vocabulary) // FLAGS.batch_size - 1 ) // FLAGS.num_steps // 10
print('ckpt save steps is', ckpt_steps)

with open(FLAGS.dictionary, encoding='utf-8') as inf:
    dictionary = json.load(inf, encoding='utf-8')

with open(FLAGS.reverse_dictionary, encoding='utf-8') as inf:
    reverse_dictionary = json.load(inf, encoding='utf-8')

print('FLAGS.learning_rate=', FLAGS.learning_rate)
print('FLAGS.batch_size=', FLAGS.batch_size)
print('FLAGS.num_steps=', FLAGS.num_steps)
print('FLAGS.embedding=', FLAGS.embedding)

model = Model(learning_rate=FLAGS.learning_rate, batch_size=FLAGS.batch_size, num_steps=FLAGS.num_steps)
model.build(FLAGS.embedding)


with tf.Session() as sess:
    summary_string_writer = tf.summary.FileWriter(FLAGS.output_dir, sess.graph)

    saver = tf.train.Saver(max_to_keep=5)
    sess.run(tf.global_variables_initializer())
    sess.run(tf.local_variables_initializer())
    logging.debug('Initialized')

    try:
        checkpoint_path = tf.train.latest_checkpoint(FLAGS.output_dir)
        saver.restore(sess, checkpoint_path)
        logging.debug('restore from [{0}]'.format(checkpoint_path))

    except Exception:
        logging.debug('no check point found....')

    for x in range(1):
        logging.debug('epoch [{0}]....'.format(x))
        state = sess.run(model.state_tensor)
        for dl in utils.get_train_data(vocabulary, batch_size=FLAGS.batch_size, num_steps=FLAGS.num_steps):

            ##################
            # Your Code here
            ##################
            feed_dict = {
            model.X : utils.index_data(dl[0], dictionary),
            model.Y : utils.index_data(dl[1], dictionary),
            model.keep_prob : 0.5,
            }
            for i, (c, h) in enumerate(model.state_tensor):
                feed_dict[c] = state[i].c  
                feed_dict[h] = state[i].h
            #################
            gs, _, state, l, summary_string = sess.run(
                [model.global_step, model.optimizer, model.outputs_state_tensor, model.loss, model.merged_summary_op], feed_dict=feed_dict)
            summary_string_writer.add_summary(summary_string, gs)

            if gs % ckpt_steps == 0:
                logging.debug('step [{0}] loss [{1}]'.format(gs, l))
                save_path = saver.save(sess, os.path.join(
                    FLAGS.output_dir, "model.ckpt"), global_step=gs)
    summary_string_writer.close()

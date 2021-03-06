#!/usr/bin/python
# coding=utf-8

import tensorflow as tf
import csv_reader
import os 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

"""
hyper-parameter setting
"""
batch_size = 20
learning_rate = 0.001
learning_round = 1000
regular_lambda = 0.01

def build_perceptron(train_set, test_set):
	"""
	build simple neural network with 3 basic layers
	framework: input: (None, 21) -> hidden: (21, 128) -> output: (128, 1)
	act-func : ReLu()
	regular  : L2 (0.01)
	"""
	train_size = len(train_set)
	test_size = len(test_set)

	train_features_matrix = []
	train_labels_matrix = []
	for i in range(train_size):
		train_features_matrix.append(train_set[i].features)
		train_labels_matrix.append([train_set[i].label])

	test_features_matrix = []
	test_labels_matrix = []
	for i in range(test_size):
		test_features_matrix.append(test_set[i].features)
		test_labels_matrix.append([test_set[i].label])

	x = tf.placeholder(tf.float32, shape=(None, 21), name="x-input")
	y = tf.placeholder(tf.float32, shape=(None, 1), name="y-input")
	
	weight_0 = tf.Variable(tf.random_uniform(shape=(21,128), minval=0, maxval=1, dtype=tf.float32))
	weight_1 = tf.Variable(tf.random_uniform(shape=(128,1), minval=0, maxval=1, dtype=tf.float32))

	# biase_0 = tf.Variable(tf.zeros([128]))
	# biase_1 = tf.Variable(tf.zeros([1]))
	biase_0 = tf.Variable(tf.random_uniform(shape=(1,128), minval=0, maxval=1, dtype=tf.float32))
	biase_1 = tf.Variable(tf.random_uniform(shape=(1,1), minval=0, maxval=1, dtype=tf.float32))
	# framework of NN
	hidden_layer = tf.nn.relu(tf.matmul(x, weight_0) + biase_0)
	y_predicted = tf.nn.relu(tf.matmul(hidden_layer, weight_1) + biase_1)

	# loss function of NN
	cross_entropy = tf.reduce_mean(tf.square(y - y_predicted)) + tf.contrib.layers.l2_regularizer(regular_lambda)(weight_0) + tf.contrib.layers.l2_regularizer(regular_lambda)(weight_1)
	train_step = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy)
	
	# # L2 regularizer
	# cross_entropy = tf.reduce_mean(y*tf.log(tf.clip_by_value(y_predicted, 1e-10, 1.0))) + tf.contrib.layers.l2_regularizer(0.5)(weight_0)
	# # exponential decay method in learning rate
	# global_step = tf.Variable(0)
	# learning_rate = tf.train.exponential_decay(0.1, global_step, 100, 0.96, staircase=True)
	# train_step = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy, global_step=global_step)

	# define the accuarcy
	# here we use the ReLu active function, then we have to transfer the original y_predicted into a new one
	# for other active functions, please refer to issue#2 "How to calculate the Precision, Recall and F1-Measure in Tensorflow?"
	# https://github.com/Gu-Youngfeng/LearningTensorflow/issues/2
	y_predicted = tf.cast(tf.not_equal(y_predicted, 0.0), tf.float32)
	correct_pred = tf.equal(y_predicted, y)
	accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

	tp = tf.reduce_sum(tf.multiply(y, y_predicted))
	tn = tf.reduce_sum(tf.cast(tf.equal(y,y_predicted), tf.float32)) - tp
	fp = tf.reduce_sum(tf.cast(tf.greater(y_predicted, y), tf.float32))
	fn = tf.reduce_sum(tf.cast(tf.greater(y, y_predicted), tf.float32))

	precision_1 = tp/(tp + fp)
	recall_1 = tp/(tp + fn)
	fmeasure_1 = precision_1*recall_1*2/(precision_1 + recall_1)

	precision_0 = tn/(tn + fn)
	recall_0 = tn/(tn + fp)
	fmeasure_0 = precision_0*recall_0*2/(precision_0 + recall_0)

	init = tf.global_variables_initializer()
	entropy_train = []
	entropy_test = []
	with tf.Session() as sess:
		sess.run(init)

		for i in range(learning_round):
			start_index = (batch_size*i)%train_size
			end_index = min(start_index+batch_size, train_size)

			sess.run(train_step, feed_dict={x:train_features_matrix[start_index:end_index], y:train_labels_matrix[start_index:end_index]})

			train_cross_entropy = sess.run(cross_entropy, feed_dict={x:train_features_matrix, y:train_labels_matrix})
			entropy_train.append(train_cross_entropy)
			test_cross_entropy = sess.run(cross_entropy, feed_dict={x:test_features_matrix, y:test_labels_matrix})
			entropy_test.append(test_cross_entropy)

			if i%50 == 0:
				print("ROUND:", i, "CROSS_ENTROPY:", train_cross_entropy, "CROSS_ENTROPY:", test_cross_entropy)

		precision_1, recall_1, fmeasure_1, precision_0, recall_0, fmeasure_0, accuracy = sess.run([precision_1, recall_1, fmeasure_1, precision_0, recall_0, fmeasure_0, accuracy], feed_dict={x:test_features_matrix, y:test_labels_matrix})
		print("[PREDICTION]:", precision_1, recall_1, fmeasure_1, precision_0, recall_0, fmeasure_0, accuracy)

		# print the predicted labels and real labels
		# print(sess.run(y_predicted, feed_dict={x:test_features_matrix, y:test_labels_matrix}))
		# print("-----")
		# print(test_labels_matrix)

	# draw the trade of cross_entropy with learining round
	import matplotlib.pyplot as plt
	x = range(len(entropy_train))
	plt.plot(x, entropy_train)
	plt.plot(x, entropy_test)
	plt.xlabel("Learning rounds")
	plt.ylabel("Cross entropy")
	plt.legend(["entropy on the training set", "entropy on the testing set"])
	plt.show()


if __name__ == "__main__":
	train_set, test_set = csv_reader.read_from_path_by_ratio("data/CM1.csv", 0.9)
	build_perceptron(train_set, test_set)



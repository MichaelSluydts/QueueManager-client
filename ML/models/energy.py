# -*- coding: utf-8 -*-
import pandas as pd
from HighThroughput.manage.calculation import setPriority, getPriority, setMultiplePriorities
from HighThroughput.ML.features.database import getFile,getResults,getComposition,getID
from HighThroughput.ML.features.elements import addElemental
from HighThroughput.utils.generic import getClass
from HighThroughput.communication.mysql import mysql_query
import sklearn.gaussian_process as gp
from scipy.stats import norm
from sklearn.decomposition import PCA
import numpy as np
from gpflowopt.domain import ContinuousParameter
from gpflowopt.design import LatinHyperCube
import gpflowopt
import json
from HighThroughput.ML.models.mf_kriging import MultiFiCoKriging


def calcML(queue, stat, modelClass='sklearn.gaussian_process.GaussianProcessRegressor', target='Ehull',
                   features=['mass', 'Ecoh', 'EN', 'IP'], N_init=50, stable_limit=0.05):
    materials = getComposition(queue, stat)

    if isinstance(materials, list):
        if isinstance(materials[0], str):
            return calcInitialMLPriority(queue, stat, features, N_init=N_init)

    if len(materials) < N_init and (isinstance(materials, pd.DataFrame) or isinstance(materials[0], dict)):
        print("skipped")
        return None

    allmats = getComposition(queue, 0)

    files_allmats = getFile(queue, 0)

    elref = set(['mass', 'Ecoh', 'EN', 'IP'])

    elfeatures = set(features).intersection(elref)

    allmats = addElemental(allmats, elfeatures)

    allfeats = [x for x in allmats.columns if ''.join([i for i in x if not i.isdigit()]) in features]

    # apply pca to all materials and to train set
    #    files_allmats.to_pickle("file_to_id")
    #    allmats[['id']+allfeats].to_pickle("allmats")

    #   ((allmats[allfeats]-allmats[allfeats].mean(axis = 0))/allmats[allfeats].std(axis = 0)).to_pickle("X_input_pca")

    pca = PCA(n_components=8)

    train_means1 = np.mean(allmats[allfeats].values, axis=0)
    train_stds1 = np.std(allmats[allfeats].values, axis=0)

    #    np.save("train_means1", train_means1)
    #    np.save("train_stds1" , train_stds1)

    X_all = pca.fit_transform((allmats[allfeats].values - train_means1) / train_stds1)

    #    np.save("X_pca", X_all)

    train_means = np.mean(X_all, axis=0)
    train_stds = np.std(X_all, axis=0)

    X = (X_all - train_means) / train_stds

    #    np.save("X_nrm", X)

    #    if not isinstance(materials, pd.DataFrame):
    #      domain = gpflowopt.domain.ContinuousParameter('x1', min(X[:,0]), max(X[:,0]))
    #
    #      for i in np.arange(1, X.shape[1]):
    #          domain += gpflowopt.domain.ContinuousParameter('x'+str(i+1), min(X[:,i]), max(X[:,i]))
    #
    #      design = LatinHyperCube(N_init, domain)
    #
    #      #X0 is the intial sampling plan in continuous space
    #      X0 = design.generate()
    #
    #      #indices will contain the indices of the materials to sample initially
    #      indices = []
    #
    #      #look for the indices of the materials that lay closest to the sample points in continuous space
    #      for x0 in X0:
    #          for j in range(X.shape[0]):
    #              index_new = np.linalg.norm(X-x0,axis=1).argsort()[j]
    #              if index_new not in indices:
    #                  indices.append(index_new)
    #                  break
    #
    #      priority = X.shape[0]*np.ones((len(indices)), dtype=int)
    #
    #    #    priority = {}
    #
    #    #    priority = np.zeros((X.shape[0]), dtype = int)
    #      #priority is put equal to X.shape to assure preference over the updated priorities based on ML
    #    #    for index in indices:
    #    #        priority[index] = X.shape[0]
    #
    #      #priority can be computed directly, without "indices", but "indices" might be useful for debugging
    #
    #      priority = pd.DataFrame({'id' : allmats.id.iloc[indices], 'priority' : priority})
    #
    #      print("priorities of initial sampling plan are set")
    #
    #      return priority

    if isinstance(materials, pd.DataFrame):
        materials = addElemental(materials, elfeatures)

    files_materials = getFile(queue, stat)

    if target in ['Ehull', 'E0', 'Eatom', 'Epure']:
        materialt = getResults(queue, stat, [target])

    materials = materials.join(materialt)

    X_train = pca.transform((materials[allfeats] - allmats[allfeats].mean(axis=0)) / allmats[allfeats].std(axis=0))

    # initialize kernel and GP
    kernel = gp.kernels.ConstantKernel() * gp.kernels.Matern(nu=5 / 2) + gp.kernels.WhiteKernel()
    model = gp.GaussianProcessRegressor(kernel=kernel,
                                        alpha=1e-5,
                                        n_restarts_optimizer=10,
                                        normalize_y=True)
    # fit model
    #    print((allmats[allfeats]-allmats[allfeats].mean(axis = 0))/allmats[allfeats].std(axis = 0))
    model.fit((X_train - train_means) / train_stds, materials[target])

    ids_done = set(
        [id for ind, id in enumerate(allmats.id) if files_allmats['file'].iloc[ind] in set(files_materials['file'])])

    ids_TBD = list(set(allmats.id).difference(ids_done))

    indices_TBD = np.array([index for index, id in enumerate(allmats.id) if id in ids_TBD])

    # get predictions and uncertainties
    mu, sigma = model.predict(X[indices_TBD], return_std=True)

    prob_stab = norm.cdf((stable_limit - mu) / sigma)

    print(np.max(prob_stab))
    #    print(files_allmats['file'].iloc[indices_TBD][prob_stab.argsort()[-1]])

    # get rank, the higher the better
    rank = prob_stab.argsort()

    # create priorities based on rank
    priority = np.zeros(X.shape[0], dtype=int)

    # The higher in the ranking the higher the priority should be
    for ind, rnk in enumerate(rank):
        priority[indices_TBD[rnk]] = ind

    priority = pd.DataFrame({'id': allmats.id, 'priority': priority})
    #    print(allmats.id)
    #    priority = pd.DataFrame({'id' : ids_TBD, 'priority' : priority})
    #    output = priority[~priority.id.isin(materials['id'])]
    return mu,sigma
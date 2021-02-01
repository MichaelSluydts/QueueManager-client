# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 15:28:56 2018

@author: Michiel
"""

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

def calcInitialMLPriority(queue,stat, features=['mass','Ecoh','EN','IP'], N_init = 50, stable_limit=0.05):

    allmats = getComposition(queue,0)
        
    files_allmats   = getFile(queue, 0)
        
    elref = set(['mass','Ecoh','EN','IP'])
    
    elfeatures = set(features).intersection(elref)
    
    allmats = addElemental(allmats,elfeatures)

    allfeats = [x for x in allmats.columns if ''.join([i for i in x if not i.isdigit()]) in features]
    
    #apply pca to all materials and to train set  
    pca = PCA(n_components=8)
    train_means1 = np.mean(allmats[allfeats].values, axis = 0)
    train_stds1  = np.std(allmats[allfeats].values , axis = 0)
     
    throwinds = np.where(train_stds1 == 0)[0]
    
    transf = np.delete(allmats[allfeats].values, throwinds, axis=1)
    train_means1 = np.delete(train_means1, throwinds)
    train_stds1  = np.delete(train_stds1, throwinds)

    
    X_all = pca.fit_transform((transf-train_means1)/train_stds1) 

    train_means = np.mean(X_all, axis = 0)
    train_stds  = np.std(X_all, axis = 0)

    X = (X_all-train_means)/train_stds   
      
    domain = gpflowopt.domain.ContinuousParameter('x1', min(X[:,0]), max(X[:,0]))

    for i in np.arange(1, X.shape[1]):
        domain += gpflowopt.domain.ContinuousParameter('x'+str(i+1), min(X[:,i]), max(X[:,i]))

    design = LatinHyperCube(N_init, domain)
    
    #X0 is the intial sampling plan in continuous space
    X0 = design.generate()
    
    indices = []
    
    for x0 in X0:
        for j in range(X.shape[0]):
            index_new = np.linalg.norm(X-x0,axis=1).argsort()[j]
            if index_new not in indices:
                indices.append(index_new)
                break      
      
    priority = X.shape[0]*np.ones((len(indices)), dtype=int)
      
    priority = pd.DataFrame({'id' : allmats.id.iloc[indices], 'priority' : priority})
      
    print("priorities of initial sampling plan are set")
    return priority
    

def calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target='Ehull',features=['mass','Ecoh','EN','IP'],N_init=50,stable_limit = 0.05):
    
    materials = getComposition(queue,stat)

    if isinstance(materials, list):
      if isinstance(materials[0], str):
        print('Initializing ML priorities.')
        return calcInitialMLPriority(queue,stat, features, N_init = N_init)

    if len(materials)<N_init and (isinstance(materials, pd.DataFrame) or isinstance(materials[0], dict)):
        print("skipped")
        return None   

    allmats = getComposition(queue,0)
        
    files_allmats   = getFile(queue, 0)
        
    elref = set(['mass','Ecoh','EN','IP'])
    
    elfeatures = set(features).intersection(elref)
        
    allmats = addElemental(allmats,elfeatures)

    allfeats = [x for x in allmats.columns if ''.join([i for i in x if not i.isdigit()]) in features]
    
    #apply pca to all materials and to train set
#    files_allmats.to_pickle("file_to_id")
#    allmats[['id']+allfeats].to_pickle("allmats")
    
 #   ((allmats[allfeats]-allmats[allfeats].mean(axis = 0))/allmats[allfeats].std(axis = 0)).to_pickle("X_input_pca")
    
    pca = PCA(n_components=8)
    
    train_means1 = np.mean(allmats[allfeats].values, axis = 0)
    train_stds1  = np.std(allmats[allfeats].values , axis = 0)
    
#    np.save("train_means1", train_means1)
#    np.save("train_stds1" , train_stds1)
    
    X_all = pca.fit_transform((allmats[allfeats].values-train_means1)/train_stds1) 

#    np.save("X_pca", X_all)

    train_means = np.mean(X_all, axis = 0)
    train_stds  = np.std(X_all, axis = 0)

    X = (X_all-train_means)/train_stds   
    
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
        materials = addElemental(materials,elfeatures)
    
    files_materials = getFile(queue, stat)
         
    if target in ['Ehull','E0','Eatom','Epure']:
        materialt = getResults(queue,stat,[target])

    materials = materials.join(materialt)

    X_train = pca.transform((materials[allfeats]-allmats[allfeats].mean(axis = 0))/allmats[allfeats].std(axis = 0))
    
    #initialize kernel and GP
    kernel = gp.kernels.ConstantKernel()*gp.kernels.Matern(nu=5/2)+gp.kernels.WhiteKernel()
    model  = gp.GaussianProcessRegressor(kernel=kernel,
                                alpha=1e-5,
                                n_restarts_optimizer=10,
                                normalize_y=True)
    #fit model
#    print((allmats[allfeats]-allmats[allfeats].mean(axis = 0))/allmats[allfeats].std(axis = 0))
    model.fit((X_train-train_means)/train_stds,materials[target])
    
    ids_done = set([id for ind, id in enumerate(allmats.id) if files_allmats['file'].iloc[ind] in set(files_materials['file'])])
    
    ids_TBD = list(set(allmats.id).difference(ids_done))

    indices_TBD = np.array([index for index, id in enumerate(allmats.id) if id in ids_TBD])
    
    #get predictions and uncertainties
    mu, sigma = model.predict(X[indices_TBD], return_std=True)

    prob_stab = norm.cdf((stable_limit-mu)/sigma)
    
    print(np.max(prob_stab))
#    print(files_allmats['file'].iloc[indices_TBD][prob_stab.argsort()[-1]])
    
    #get rank, the higher the better
    rank = prob_stab.argsort() 
    
    #create priorities based on rank 
    priority = np.zeros(X.shape[0], dtype=int)
    
    #The higher in the ranking the higher the priority should be 
    for ind, rnk in enumerate(rank):
        priority[indices_TBD[rnk]] = ind

    priority = pd.DataFrame({'id' : allmats.id, 'priority' : priority})
#    print(allmats.id)    
#    priority = pd.DataFrame({'id' : ids_TBD, 'priority' : priority})
#    output = priority[~priority.id.isin(materials['id'])]
    return priority

def calcMLPriority_mf(queue,stats,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target='Ehull',features=['mass','Ecoh','EN','IP'],N_init=50,stable_limit = 0.05):

    threshold = 0.1

    if not isinstance(stats, list):
        stats = [stats]
    else:
        stats = sorted(stats)

    materials = {stat:getComposition(queue,stat) for stat in stats}
    
    if isinstance(materials[stats[0]], list):
      if isinstance(materials[stats[0]][0], str):
        return calcInitialMLPriority(queue,stats[0], features, N_init = N_init)

    if len(materials[stats[0]])<N_init and (isinstance(materials[stats[0]], pd.DataFrame) or isinstance(materials[stats[0]][0], dict)):
        print("skipped")
        return None  
    
    allmats = getComposition(queue,0)
        
    files_allmats = getFile(queue, 0)
    
    allmats = allmats.join(files_allmats)
        
    allmats = allmats.set_index("file")    
        
    elref = set(['mass','Ecoh','EN','IP'])
    
    elfeatures = set(features).intersection(elref)
       
    elfeatures = list(elfeatures)
    allmats = addElemental(allmats,elfeatures)
    
    allfeats = [x for x in allmats.columns if ''.join([i for i in x if not i.isdigit()]) in features]    
    
    n_feats = 8 
    pca = PCA(n_components=n_feats)
    
    train_means1 = np.mean(allmats[allfeats].values, axis = 0)
    train_stds1  = np.std(allmats[allfeats].values , axis = 0)
    
    throwinds = np.where(train_stds1 == 0)[0]
    
    transf = np.delete(allmats[allfeats].values, throwinds, axis=1)
    train_means1 = np.delete(train_means1, throwinds)
    train_stds1  = np.delete(train_stds1, throwinds)

    X_all = pca.fit_transform((transf-train_means1)/train_stds1) 

#    np.save("X_pca", X_all)

    train_means = np.mean(X_all, axis = 0)
    train_stds  = np.std(X_all, axis = 0)

    X = (X_all-train_means)/train_stds
    
    allmats = allmats.assign(x0 = X[:,0], x1 = X[:,1], x2 = X[:,2], x3 = X[:,3],\
                    x4 = X[:,4], x5 = X[:,5], x6 = X[:,6], x7 = X[:,7])

    feat_names = ["x"+str(i) for i in range(n_feats)]   
    
    files_materials = {stat: getFile(queue, stat) for stat in stats}
    
    for stat in stats:     
#        if isinstance(materials[stat], pd.DataFrame):  
#            materials[stat] = addElemental(materials[stat],elfeatures)
        mat_files = getFile(queue, stat)
        
        materials[stat] = materials[stat].join(mat_files)
        
        materials[stat] = materials[stat].set_index("file")
        if target in ['Ehull','E0','Eatom','Epure']:
            materialt = getResults(queue,stat,[target]).set_index("file")

        materials[stat] = materials[stat].join(materialt)

    X_lvls = []
    Y_lvls = []
    inds_prev = set()
    #stats_skipped = 0

    for i, stat in enumerate(stats[::-1]):
        ids_done = set([id for ind, id in enumerate(allmats.index) if files_allmats['file'].iloc[ind] in set(files_materials[stat]['file'])])    
        inds = ids_done.difference(inds_prev)
        if len(inds)>0:
#            print(inds)
#            print(list(materials[stat].index))
#            print(list(allmats.index))
#            print(inds)
#            print(files_materials[stat]['file'].values)
#            print(files_allmats['file'].loc[inds].values)
#            inds_target = [np.where(files_materials[stat]['file'].values == files_allmats['file'].loc[ind])[0][0] for ind in inds]
#            print(inds_target)
            X_lvl = [allmats[feat_names].reindex(inds).values]
#            print(materials[stat][target].values)
            Y_lvl = [materials[stat][target].reindex(inds).values]
            if np.isfinite(Y_lvl).all() and np.isfinite(X_lvl).all():
              inds_prev = inds_prev.union(inds)
              #print('i',i,'stat',stat,'level',len(X_lvl),'levels',len(X_lvls))
#              print("indices updated")
              #if i>0:
              #    X_lvl.append(X_lvls[i-1-stats_skipped])
              #    Y_lvl.append(Y_lvls[i-1-stats_skipped])
              if len(X_lvls)>0 and len(Y_lvls)>0:
                  X_lvl.append(X_lvls[-1])
                  Y_lvl.append(Y_lvls[-1])
              X_lvls.append(np.vstack(X_lvl))
              Y_lvls.append(np.hstack(Y_lvl))
              #print('i',i,'stat',stat,'level',len(X_lvl),'levels',len(X_lvls))
            #else:
              #print('Hurray, for I have skipped')
              #stats_skipped += 1 
        #else:
            #stats_skipped += 1
#            print(X_lvl)
#            print(Y_lvl)

    model = MultiFiCoKriging(regr = 'linear', rho_regr = 'linear')
#    print("preprocess time: " + str(time.time()-start)) 
    #fit model
    
    try:
      model.fit(X_lvls[::-1], Y_lvls[::-1])
    except (ValueError, IndexError) as e:
      print(e)
      print("priorities have not been updated, because of NaNs in data. Please check the calculation results.")
      return None
      
    indices_TBD = list(set(allmats.index).difference(inds_prev))
       
    
    #get predictions and uncertainties
    mu, sigma = model.predict(allmats[feat_names].loc[indices_TBD].values)

    mu = mu.flatten()
    sigma = sigma.flatten()

    prob_stab = norm.cdf((stable_limit-mu)/sigma)
    max_prob_stab = np.max(prob_stab)
    print(max_prob_stab)
#    print(files_allmats['file'].iloc[indices_TBD][prob_stab.argsort()[-1]])
    
    #get rank, the higher the better
    if max_prob_stab>threshold:
      rank = prob_stab.argsort()
    else:
      print("uncertainty sampled")
      rank = sigma.argsort()
#    print(rank) 
    
    #create priorities based on rank
    priority = np.zeros(len(rank), dtype = int)
    ids = np.zeros(len(rank), dtype = int)
#    priority = pd.DataFrame(np.zeros((X.shape[0], 2), dtype=int),index=allmats.index, columns = ["id", "priority"])
#    
#    #The higher in the ranking the higher the priority should be 
#    for ind, rnk in enumerate(rank):
#        priority["priority"].loc[indices_TBD[rnk]] = ind
#        priority["id"].loc[indices_TBD[rnk]] = allmats.id.loc[indices_TBD[rnk]]
    indices_all = pd.Index(allmats.index)

    for ind, rnk in enumerate(rank):
        loc = indices_all.get_loc(indices_TBD[rnk])
        priority[ind] = ind
        ids[ind] = allmats.id.iloc[loc]
    
#    print(priority)
#    priority = pd.DataFrame({'id' : allmats.id, 'priority' : priority.values})    
#    print(priority)
    priorities = pd.DataFrame({'id' : ids, 'priority' : priority})
#    output = priority[~priority.id.isin(materials['id'])]
    return priorities

def updateMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target='Ehull',features=['mass','Ecoh','EN','IP'],maxParallel=30,N_init=50):
    priorities = calcMLPriority_mf(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target=target,features=features,N_init=N_init)
    if isinstance(priorities, pd.DataFrame):
       setMultiplePriorities(priorities)
#        priorities = priorities.sort_values(ascending=False,by='priority')
#        print(priorities)
#        for i,p in priorities.iterrows():
#            print(i)
#            setPriority(p['priority'], p['id'])

def setMLPriority(queue, stat, features=['mass','Ecoh','EN','IP'], N_init = 50,stable_limit=0.05):
    priorities = calcInitialMLPriority(queue, stat, features, N_init,stable_limit)
    setMultiplePriorities(priorities)

from nose import SkipTest
from functools import wraps
from tempfile import mkdtemp
from scipy.stats import mode
from sklearn.cluster import KMeans
from sklearn.manifold.t_sne import trustworthiness
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.utils import shuffle
from sklearn.neighbors import KDTree, BallTree
from sklearn.metrics import pairwise_distances, adjusted_rand_score
from sklearn.utils.testing import (
    assert_equal,
    assert_array_equal,
    assert_almost_equal,
    assert_array_almost_equal,
    assert_raises,
    assert_in,
    assert_not_in,
    assert_no_warnings,
)
from sklearn.utils.estimator_checks import check_estimator
from scipy import stats
from scipy import sparse
from scipy.spatial import distance
import numpy as np
import os.path
from nose.tools import assert_greater_equal
from nose.tools import assert_less

"""
Tests for UMAP to ensure things are working as expected.
"""
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from sklearn import datasets

import umap.distances as dist
import umap.sparse as spdist
import umap.validation as valid
from umap.nndescent import initialized_nnd_search, initialise_search
from umap.sparse_nndescent import (
    sparse_initialized_nnd_search,
    sparse_initialise_search,
)
from umap.utils import deheap_sort
from umap.umap_ import (
    INT32_MAX,
    INT32_MIN,
    make_forest,
    rptree_leaf_array,
    nearest_neighbors,
    smooth_knn_dist,
    fuzzy_simplicial_set,
    UMAP,
    DataFrameUMAP,
    _HAVE_PYNNDESCENT,
)

np.random.seed(42)
spatial_data = np.random.randn(10, 20)
spatial_data = np.vstack(
    [spatial_data, np.zeros((2, 20))]
)  # Add some all zero data for corner case test
binary_data = np.random.choice(a=[False, True], size=(10, 20), p=[0.66, 1 - 0.66])
binary_data = np.vstack(
    [binary_data, np.zeros((2, 20), dtype="bool")]
)  # Add some all zero data for corner case test
sparse_spatial_data = sparse.csr_matrix(spatial_data * binary_data)
sparse_binary_data = sparse.csr_matrix(binary_data)

nn_data = np.random.uniform(0, 1, size=(1000, 5))
nn_data = np.vstack(
    [nn_data, np.zeros((2, 5))]
)  # Add some all zero data for corner case test
binary_nn_data = np.random.choice(a=[False, True], size=(1000, 5), p=[0.66, 1 - 0.66])
binary_nn_data = np.vstack(
    [binary_nn_data, np.zeros((2, 5), dtype="bool")]
)  # Add some all zero data for corner case test
sparse_test_data = sparse.csr_matrix(nn_data * binary_nn_data)
sparse_nn_data = sparse.random(1000, 50, density=0.5, format="csr")

iris = datasets.load_iris()
iris_selection = np.random.choice([True, False], 150, replace=True, p=[0.75, 0.25])

iris_model = UMAP(n_neighbors=10, min_dist=0.01, random_state=42).fit(iris.data)

supervised_iris_model = UMAP(
    n_neighbors=10, min_dist=0.01, n_epochs=200, random_state=42
).fit(iris.data, iris.target)

spatial_distances = (
    "euclidean",
    "manhattan",
    "chebyshev",
    "minkowski",
    "hamming",
    "canberra",
    "braycurtis",
    "cosine",
    "correlation",
)

binary_distances = (
    "jaccard",
    "matching",
    "dice",
    "kulsinski",
    "rogerstanimoto",
    "russellrao",
    "sokalmichener",
    "sokalsneath",
    "yule",
)

######## Create a bunch of data with repeats ############
# Dense data for testing small n
repetition_dense = np.array(
    [
        [5, 6, 7, 8],
        [5, 6, 7, 8],
        [5, 6, 7, 8],
        [5, 6, 7, 8],
        [5, 6, 7, 8],
        [5, 6, 7, 8],
        [1, 1, 1, 1],
        [1, 2, 3, 4],
        [1, 1, 2, 1],
    ]
)

# Sparse data for testing
spatial_repeats = np.vstack(
    [np.repeat(spatial_data[0:2], [2, 0], axis=0), spatial_data, np.zeros((2, 20))]
)  # Add some all zero data for corner case test.  Make the first three rows identical
binary_repeats = np.vstack(
    [
        np.repeat(binary_data[0:2], [2, 0], axis=0),
        binary_data,
        np.zeros((2, 20), dtype="bool"),
    ]
)  # Add some all zero data for corner case test.  Make the first three rows identical
sparse_spatial_data_repeats = sparse.csr_matrix(spatial_repeats * binary_repeats)
sparse_binary_data_repeats = sparse.csr_matrix(binary_repeats)

######################### Spatial test cases ###############################
# Use force_approximation_algorithm in order to test the region of the code that is called for n>4096
def repeated_points_large_sparse_spatial():
    model = UMAP(n_neighbors=3, unique=True, force_approximation_algorithm=True).fit(
        sparse_spatial_data_repeats
    )
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


def repeated_points_small_sparse_spatial():
    model = UMAP(n_neighbors=3, unique=True).fit(sparse_spatial_data_repeats)
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


# Use force_approximation_algorithm in order to test the region of the code that is called for n>4096
def repeated_points_large_dense_spatial():
    model = UMAP(n_neighbors=3, unique=True, force_approximation_algorithm=True).fit(
        spatial_repeats
    )
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


def repeated_points_small_dense_spatial():
    model = UMAP(n_neighbors=3, unique=True).fit(spatial_repeats)
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


######################## Binary test cases ###################################
# Use force_approximation_algorithm in order to test the region of the code that is called for n>4096
def repeated_points_large_sparse_binary():
    model = UMAP(n_neighbors=3, unique=True, force_approximation_algorithm=True).fit(
        sparse_binary_data_repeats
    )
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


def repeated_points_small_sparse_binary():
    model = UMAP(n_neighbors=3, unique=True).fit(sparse_binary_data_repeats)
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


# Use force_approximation_algorithm in order to test the region of the code that is called for n>4096
def repeated_points_large_dense_binary():
    model = UMAP(n_neighbors=3, unique=True, force_approximation_algorithm=True).fit(
        binary_repeats
    )
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


def repeated_points_small_dense_binary():
    model = UMAP(n_neighbors=3, unique=True).fit(binary_repeats)
    # assert_equal(np.unique(binary_repeats[0:2], axis=0).shape[0],1)
    assert_equal(np.unique(model.embedding_[0:2], axis=0).shape[0], 1)


#######################################################################################
# This should test whether the n_neighbours are being reduced properly when your n_neighbours is larger
# than the uniqued data set size
def repeated_points_large_n():
    model = UMAP(n_neighbors=5, unique=True).fit(repetition_dense)
    assert_equal(model._n_neighbors, 3)


def spatial_check(metric):
    dist_matrix = pairwise_distances(spatial_data, metric=metric)
    # scipy is bad sometimes
    if metric == "braycurtis":
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 0.0
    if metric in ("cosine", "correlation"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 1.0
        # And because distance between all zero vectors should be zero
        dist_matrix[10, 11] = 0.0
        dist_matrix[11, 10] = 0.0
    dist_function = dist.named_distances[metric]
    test_matrix = np.array(
        [
            [
                dist_function(spatial_data[i], spatial_data[j])
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric {}".format(metric),
    )


def binary_check(metric):
    dist_matrix = pairwise_distances(binary_data, metric=metric)
    if metric in ("jaccard", "dice", "sokalsneath", "yule"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 0.0
    if metric in ("kulsinski", "russellrao"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 0.0
        # And because distance between all zero vectors should be zero
        dist_matrix[10, 11] = 0.0
        dist_matrix[11, 10] = 0.0
    dist_function = dist.named_distances[metric]
    test_matrix = np.array(
        [
            [
                dist_function(binary_data[i], binary_data[j])
                for j in range(binary_data.shape[0])
            ]
            for i in range(binary_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric {}".format(metric),
    )


def sparse_spatial_check(metric):
    if metric in spdist.sparse_named_distances:
        dist_matrix = pairwise_distances(sparse_spatial_data.todense(), metric=metric)
    if metric in ("braycurtis", "dice", "sokalsneath", "yule"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 0.0
    if metric in ("cosine", "correlation", "kulsinski", "russellrao"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 1.0
        # And because distance between all zero vectors should be zero
        dist_matrix[10, 11] = 0.0
        dist_matrix[11, 10] = 0.0

    dist_function = spdist.sparse_named_distances[metric]
    if metric in spdist.sparse_need_n_features:
        test_matrix = np.array(
            [
                [
                    dist_function(
                        sparse_spatial_data[i].indices,
                        sparse_spatial_data[i].data,
                        sparse_spatial_data[j].indices,
                        sparse_spatial_data[j].data,
                        sparse_spatial_data.shape[1],
                    )
                    for j in range(sparse_spatial_data.shape[0])
                ]
                for i in range(sparse_spatial_data.shape[0])
            ]
        )
    else:
        test_matrix = np.array(
            [
                [
                    dist_function(
                        sparse_spatial_data[i].indices,
                        sparse_spatial_data[i].data,
                        sparse_spatial_data[j].indices,
                        sparse_spatial_data[j].data,
                    )
                    for j in range(sparse_spatial_data.shape[0])
                ]
                for i in range(sparse_spatial_data.shape[0])
            ]
        )

    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Sparse distances don't match " "for metric {}".format(metric),
    )


def sparse_binary_check(metric):
    if metric in spdist.sparse_named_distances:
        dist_matrix = pairwise_distances(sparse_binary_data.todense(), metric=metric)
    if metric in ("jaccard", "dice", "sokalsneath", "yule"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 0.0
    if metric in ("kulsinski", "russellrao"):
        dist_matrix[np.where(~np.isfinite(dist_matrix))] = 1.0
        # And because distance between all zero vectors should be zero
        dist_matrix[10, 11] = 0.0
        dist_matrix[11, 10] = 0.0

    dist_function = spdist.sparse_named_distances[metric]
    if metric in spdist.sparse_need_n_features:
        test_matrix = np.array(
            [
                [
                    dist_function(
                        sparse_binary_data[i].indices,
                        sparse_binary_data[i].data,
                        sparse_binary_data[j].indices,
                        sparse_binary_data[j].data,
                        sparse_binary_data.shape[1],
                    )
                    for j in range(sparse_binary_data.shape[0])
                ]
                for i in range(sparse_binary_data.shape[0])
            ]
        )
    else:
        test_matrix = np.array(
            [
                [
                    dist_function(
                        sparse_binary_data[i].indices,
                        sparse_binary_data[i].data,
                        sparse_binary_data[j].indices,
                        sparse_binary_data[j].data,
                    )
                    for j in range(sparse_binary_data.shape[0])
                ]
                for i in range(sparse_binary_data.shape[0])
            ]
        )

    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Sparse distances don't match " "for metric {}".format(metric),
    )


# Transform isn't stable under batching; hard to opt out of this.
@SkipTest
def test_scikit_learn_compatibility():
    check_estimator(UMAP)


def test_nn_descent_neighbor_accuracy():
    knn_indices, knn_dists, _ = nearest_neighbors(
        nn_data, 10, "euclidean", {}, False, np.random
    )

    tree = KDTree(nn_data)
    true_indices = tree.query(nn_data, 10, return_distance=False)

    num_correct = 0.0
    for i in range(nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (nn_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.89,
        "NN-descent did not get 99% " "accuracy on nearest neighbors",
    )


def test_nn_descent_neighbor_accuracy_low_memory():
    knn_indices, knn_dists, _ = nearest_neighbors(
        nn_data, 10, "euclidean", {}, False, np.random, low_memory=True
    )

    tree = KDTree(nn_data)
    true_indices = tree.query(nn_data, 10, return_distance=False)

    num_correct = 0.0
    for i in range(nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (nn_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.89,
        "NN-descent did not get 99% " "accuracy on nearest neighbors",
    )


def test_angular_nn_descent_neighbor_accuracy():
    knn_indices, knn_dists, _ = nearest_neighbors(
        nn_data, 10, "cosine", {}, True, np.random
    )

    angular_data = normalize(nn_data, norm="l2")
    tree = KDTree(angular_data)
    true_indices = tree.query(angular_data, 10, return_distance=False)

    num_correct = 0.0
    for i in range(nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (nn_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.89,
        "NN-descent did not get 99% " "accuracy on nearest neighbors",
    )


def test_sparse_nn_descent_neighbor_accuracy():
    knn_indices, knn_dists, _ = nearest_neighbors(
        sparse_nn_data, 20, "euclidean", {}, False, np.random
    )

    tree = KDTree(sparse_nn_data.todense())
    true_indices = tree.query(sparse_nn_data.todense(), 10, return_distance=False)

    num_correct = 0.0
    for i in range(sparse_nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (sparse_nn_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.90,
        "Sparse NN-descent did not get " "99% accuracy on nearest " "neighbors",
    )


def test_sparse_nn_descent_neighbor_accuracy_low_memory():
    knn_indices, knn_dists, _ = nearest_neighbors(
        sparse_nn_data, 20, "euclidean", {}, False, np.random, low_memory=True
    )

    tree = KDTree(sparse_nn_data.todense())
    true_indices = tree.query(sparse_nn_data.todense(), 10, return_distance=False)

    num_correct = 0.0
    for i in range(sparse_nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (sparse_nn_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.90,
        "Sparse NN-descent did not get " "99% accuracy on nearest " "neighbors",
    )


@SkipTest
def test_sparse_angular_nn_descent_neighbor_accuracy():
    knn_indices, knn_dists, _ = nearest_neighbors(
        sparse_nn_data, 20, "cosine", {}, True, np.random
    )

    angular_data = normalize(sparse_nn_data, norm="l2").toarray()
    tree = KDTree(angular_data)
    true_indices = tree.query(angular_data, 10, return_distance=False)

    num_correct = 0.0
    for i in range(sparse_nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (sparse_nn_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.90,
        "NN-descent did not get 99% " "accuracy on nearest neighbors",
    )


def test_smooth_knn_dist_l1norms():
    knn_indices, knn_dists, _ = nearest_neighbors(
        nn_data, 10, "euclidean", {}, False, np.random
    )
    sigmas, rhos = smooth_knn_dist(knn_dists, 10.0)
    shifted_dists = knn_dists - rhos[:, np.newaxis]
    shifted_dists[shifted_dists < 0.0] = 0.0
    vals = np.exp(-(shifted_dists / sigmas[:, np.newaxis]))
    norms = np.sum(vals, axis=1)

    assert_array_almost_equal(
        norms,
        1.0 + np.log2(10) * np.ones(norms.shape[0]),
        decimal=3,
        err_msg="Smooth knn-dists does not give expected" "norms",
    )


def test_nn_descent_neighbor_accuracy_callable_metric():
    knn_indices, knn_dists, _ = nearest_neighbors(
        nn_data, 10, dist.euclidean, {}, False, np.random
    )

    tree = KDTree(nn_data)
    true_indices = tree.query(nn_data, 10, return_distance=False)

    num_correct = 0.0
    for i in range(nn_data.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], knn_indices[i]))

    percent_correct = num_correct / (spatial_data.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.99,
        "NN-descent did not get 99% "
        "accuracy on nearest neighbors with callable metric",
    )


def test_smooth_knn_dist_l1norms_w_connectivity():
    knn_indices, knn_dists, _ = nearest_neighbors(
        nn_data, 10, "euclidean", {}, False, np.random
    )
    sigmas, rhos = smooth_knn_dist(knn_dists, 10.0, local_connectivity=1.75)
    shifted_dists = knn_dists - rhos[:, np.newaxis]
    shifted_dists[shifted_dists < 0.0] = 0.0
    vals = np.exp(-(shifted_dists / sigmas[:, np.newaxis]))
    norms = np.sum(vals, axis=1)

    assert_array_almost_equal(
        norms,
        1.0 + np.log2(10) * np.ones(norms.shape[0]),
        decimal=3,
        err_msg="Smooth knn-dists does not give expected"
        "norms for local_connectivity=1.75",
    )

    # sigmas, rhos = smooth_knn_dist(knn_dists, 10, local_connectivity=0.75)
    # shifted_dists = knn_dists - rhos[:, np.newaxis]
    # shifted_dists[shifted_dists < 0.0] = 0.0
    # vals = np.exp(-(shifted_dists / sigmas[:, np.newaxis]))
    # norms = np.sum(vals, axis=1)
    # diff = np.mean(norms) - (1.0 + np.log2(10))
    #
    # assert_almost_equal(diff, 0.0, decimal=1,
    #                     err_msg='Smooth knn-dists does not give expected'
    #                             'norms for local_connectivity=0.75')


def test_nn_search():
    train = nn_data[100:]
    test = nn_data[:100]

    (knn_indices, knn_dists, rp_forest) = nearest_neighbors(
        train, 10, "euclidean", {}, False, np.random, use_pynndescent=False,
    )

    graph = fuzzy_simplicial_set(
        nn_data,
        10,
        np.random,
        "euclidean",
        {},
        knn_indices,
        knn_dists,
        False,
        1.0,
        1.0,
        False,
    )

    search_graph = sparse.lil_matrix((train.shape[0], train.shape[0]), dtype=np.int8)
    search_graph.rows = knn_indices
    search_graph.data = (knn_dists != 0).astype(np.int8)
    search_graph = search_graph.maximum(search_graph.transpose()).tocsr()

    rng_state = np.random.randint(INT32_MIN, INT32_MAX, 3).astype(np.int64)
    init = initialise_search(
        rp_forest, train, test, int(10 * 3), rng_state, dist.euclidean
    )
    result = initialized_nnd_search(
        train, search_graph.indptr, search_graph.indices, init, test, dist.euclidean
    )

    indices, dists = deheap_sort(result)
    indices = indices[:, :10]

    tree = KDTree(train)
    true_indices = tree.query(test, 10, return_distance=False)

    num_correct = 0.0
    for i in range(test.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], indices[i]))

    percent_correct = num_correct / (test.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.99,
        "Sparse NN-descent did not get " "99% accuracy on nearest " "neighbors",
    )


def test_sparse_nn_search():
    train = sparse_nn_data[100:]
    test = sparse_nn_data[:100]
    (knn_indices, knn_dists, rp_forest) = nearest_neighbors(
        train, 15, "euclidean", {}, False, np.random, use_pynndescent=False,
    )

    graph = fuzzy_simplicial_set(
        nn_data,
        15,
        np.random,
        "euclidean",
        {},
        knn_indices,
        knn_dists,
        False,
        1.0,
        1.0,
        False,
    )

    search_graph = sparse.lil_matrix((train.shape[0], train.shape[0]), dtype=np.int8)
    search_graph.rows = knn_indices
    search_graph.data = (knn_dists != 0).astype(np.int8)
    search_graph = search_graph.maximum(search_graph.transpose()).tocsr()

    rng_state = np.random.randint(INT32_MIN, INT32_MAX, 3).astype(np.int64)
    init = sparse_initialise_search(
        rp_forest,
        train.indices,
        train.indptr,
        train.data,
        test.indices,
        test.indptr,
        test.data,
        int(10 * 6),
        rng_state,
        spdist.sparse_euclidean,
    )
    result = sparse_initialized_nnd_search(
        train.indices,
        train.indptr,
        train.data,
        search_graph.indptr,
        search_graph.indices,
        init,
        test.indices,
        test.indptr,
        test.data,
        spdist.sparse_euclidean,
    )

    indices, dists = deheap_sort(result)
    indices = indices[:, :10]

    tree = KDTree(train.toarray())
    true_indices = tree.query(test.toarray(), 10, return_distance=False)

    num_correct = 0.0
    for i in range(test.shape[0]):
        num_correct += np.sum(np.in1d(true_indices[i], indices[i]))

    percent_correct = num_correct / (test.shape[0] * 10)
    assert_greater_equal(
        percent_correct,
        0.85,
        "Sparse NN-descent did not get " "85% accuracy on nearest " "neighbors",
    )


def test_euclidean():
    spatial_check("euclidean")


def test_manhattan():
    spatial_check("manhattan")


def test_chebyshev():
    spatial_check("chebyshev")


def test_minkowski():
    spatial_check("minkowski")


def test_hamming():
    spatial_check("hamming")


def test_canberra():
    spatial_check("canberra")


def test_braycurtis():
    spatial_check("braycurtis")


def test_cosine():
    spatial_check("cosine")


def test_correlation():
    spatial_check("correlation")


def test_jaccard():
    binary_check("jaccard")


def test_matching():
    binary_check("matching")


def test_dice():
    binary_check("dice")


def test_kulsinski():
    binary_check("kulsinski")


def test_rogerstanimoto():
    binary_check("rogerstanimoto")


def test_russellrao():
    binary_check("russellrao")


def test_sokalmichener():
    binary_check("sokalmichener")


def test_sokalsneath():
    binary_check("sokalsneath")


def test_yule():
    binary_check("yule")


def test_sparse_euclidean():
    sparse_spatial_check("euclidean")


def test_sparse_manhattan():
    sparse_spatial_check("manhattan")


def test_sparse_chebyshev():
    sparse_spatial_check("chebyshev")


def test_sparse_minkowski():
    sparse_spatial_check("minkowski")


def test_sparse_hamming():
    sparse_spatial_check("hamming")


def test_sparse_canberra():
    sparse_spatial_check("canberra")


def test_sparse_cosine():
    sparse_spatial_check("cosine")


def test_sparse_correlation():
    sparse_spatial_check("correlation")


def test_sparse_jaccard():
    sparse_binary_check("jaccard")


def test_sparse_matching():
    sparse_binary_check("matching")


def test_sparse_dice():
    sparse_binary_check("dice")


def test_sparse_kulsinski():
    sparse_binary_check("kulsinski")


def test_sparse_rogerstanimoto():
    sparse_binary_check("rogerstanimoto")


def test_sparse_russellrao():
    sparse_binary_check("russellrao")


def test_sparse_sokalmichener():
    sparse_binary_check("sokalmichener")


def test_sparse_sokalsneath():
    sparse_binary_check("sokalsneath")


def test_seuclidean():
    v = np.abs(np.random.randn(spatial_data.shape[1]))
    dist_matrix = pairwise_distances(spatial_data, metric="seuclidean", V=v)
    test_matrix = np.array(
        [
            [
                dist.standardised_euclidean(spatial_data[i], spatial_data[j], v)
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric seuclidean",
    )


def test_weighted_minkowski():
    v = np.abs(np.random.randn(spatial_data.shape[1]))
    dist_matrix = pairwise_distances(spatial_data, metric="wminkowski", w=v, p=3)
    test_matrix = np.array(
        [
            [
                dist.weighted_minkowski(spatial_data[i], spatial_data[j], v, p=3)
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric weighted_minkowski",
    )


def test_mahalanobis():
    v = np.cov(np.transpose(spatial_data))
    dist_matrix = pairwise_distances(spatial_data, metric="mahalanobis", VI=v)
    test_matrix = np.array(
        [
            [
                dist.mahalanobis(spatial_data[i], spatial_data[j], v)
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric mahalanobis",
    )


def test_haversine():
    tree = BallTree(spatial_data[:, :2], metric="haversine")
    dist_matrix, _ = tree.query(spatial_data[:, :2], k=spatial_data.shape[0])
    test_matrix = np.array(
        [
            [
                dist.haversine(spatial_data[i, :2], spatial_data[j, :2])
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    test_matrix.sort(axis=1)
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric haversine",
    )


def test_hellinger():
    hellinger_data = np.abs(spatial_data[:-2].copy())
    hellinger_data = hellinger_data / hellinger_data.sum(axis=1)[:, np.newaxis]
    hellinger_data = np.sqrt(hellinger_data)
    dist_matrix = hellinger_data @ hellinger_data.T
    dist_matrix = 1.0 - dist_matrix
    dist_matrix = np.sqrt(dist_matrix)
    # Correct for nan handling
    dist_matrix[np.isnan(dist_matrix)] = 0.0

    test_matrix = dist.pairwise_special_metric(np.abs(spatial_data[:-2]))

    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric hellinger",
    )

    # Ensure ll_dirichlet runs
    test_matrix = dist.pairwise_special_metric(
        np.abs(spatial_data[:-2]), metric="ll_dirichlet"
    )


def test_sparse_hellinger():
    dist_matrix = dist.pairwise_special_metric(
        np.abs(sparse_spatial_data[:-2].toarray())
    )
    test_matrix = np.array(
        [
            [
                spdist.sparse_hellinger(
                    np.abs(sparse_spatial_data[i]).indices,
                    np.abs(sparse_spatial_data[i]).data,
                    np.abs(sparse_spatial_data[j]).indices,
                    np.abs(sparse_spatial_data[j]).data,
                )
                for j in range(sparse_spatial_data.shape[0] - 2)
            ]
            for i in range(sparse_spatial_data.shape[0] - 2)
        ]
    )

    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Sparse distances don't match " "for metric hellinger",
        decimal=4,
    )

    # Ensure ll_dirichlet runs
    test_matrix = np.array(
        [
            [
                spdist.sparse_ll_dirichlet(
                    sparse_spatial_data[i].indices,
                    sparse_spatial_data[i].data,
                    sparse_spatial_data[j].indices,
                    sparse_spatial_data[j].data,
                )
                for j in range(sparse_spatial_data.shape[0])
            ]
            for i in range(sparse_spatial_data.shape[0])
        ]
    )


def test_grad_metrics_match_metrics():
    for metric in dist.named_distances_with_gradients:
        if metric in spatial_distances:
            dist_matrix = pairwise_distances(spatial_data, metric=metric)
            # scipy is bad sometimes
            if metric == "braycurtis":
                dist_matrix[np.where(~np.isfinite(dist_matrix))] = 0.0
            if metric in ("cosine", "correlation"):
                dist_matrix[np.where(~np.isfinite(dist_matrix))] = 1.0
                # And because distance between all zero vectors should be zero
                dist_matrix[10, 11] = 0.0
                dist_matrix[11, 10] = 0.0

            dist_function = dist.named_distances_with_gradients[metric]
            test_matrix = np.array(
                [
                    [
                        dist_function(spatial_data[i], spatial_data[j])[0]
                        for j in range(spatial_data.shape[0])
                    ]
                    for i in range(spatial_data.shape[0])
                ]
            )
            assert_array_almost_equal(
                test_matrix,
                dist_matrix,
                err_msg="Distances with grad don't match "
                "for metric {}".format(metric),
            )

    # Handle the few special distances separately
    # SEuclidean
    v = np.abs(np.random.randn(spatial_data.shape[1]))
    dist_matrix = pairwise_distances(spatial_data, metric="seuclidean", V=v)
    test_matrix = np.array(
        [
            [
                dist.standardised_euclidean_grad(spatial_data[i], spatial_data[j], v)[0]
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric seuclidean",
    )

    # Weighted minkowski
    dist_matrix = pairwise_distances(spatial_data, metric="wminkowski", w=v, p=3)
    test_matrix = np.array(
        [
            [
                dist.weighted_minkowski_grad(spatial_data[i], spatial_data[j], v, p=3)[
                    0
                ]
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric weighted_minkowski",
    )
    # Mahalanobis
    v = np.abs(np.random.randn(spatial_data.shape[1], spatial_data.shape[1]))
    dist_matrix = pairwise_distances(spatial_data, metric="mahalanobis", VI=v)
    test_matrix = np.array(
        [
            [
                dist.mahalanobis_grad(spatial_data[i], spatial_data[j], v)[0]
                for j in range(spatial_data.shape[0])
            ]
            for i in range(spatial_data.shape[0])
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric mahalanobis",
    )

    # Hellinger
    dist_matrix = dist.pairwise_special_metric(
        np.abs(spatial_data[:-2]), np.abs(spatial_data[:-2])
    )
    test_matrix = np.array(
        [
            [
                dist.hellinger_grad(np.abs(spatial_data[i]), np.abs(spatial_data[j]))[0]
                for j in range(spatial_data.shape[0] - 2)
            ]
            for i in range(spatial_data.shape[0] - 2)
        ]
    )
    assert_array_almost_equal(
        test_matrix,
        dist_matrix,
        err_msg="Distances don't match " "for metric hellinger",
    )


def test_umap_sparse_trustworthiness():
    embedding = UMAP(n_neighbors=10).fit_transform(sparse_test_data[:100])
    trust = trustworthiness(sparse_test_data[:100].toarray(), embedding, 10)
    assert_greater_equal(
        trust,
        0.91,
        "Insufficiently trustworthy embedding for"
        "sparse test dataset: {}".format(trust),
    )


def test_umap_trustworthiness_fast_approx():
    data = nn_data[:50]
    embedding = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        random_state=42,
        n_epochs=100,
        force_approximation_algorithm=True,
    ).fit_transform(data)
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.75,
        "Insufficiently trustworthy embedding for" "nn dataset: {}".format(trust),
    )


def test_umap_trustworthiness_random_init():
    data = nn_data[:50]
    embedding = UMAP(
        n_neighbors=10, min_dist=0.01, random_state=42, init="random"
    ).fit_transform(data)
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.75,
        "Insufficiently trustworthy embedding for" "nn dataset: {}".format(trust),
    )


def test_supervised_umap_trustworthiness():
    data, labels = datasets.make_blobs(50, cluster_std=0.5, random_state=42)
    embedding = UMAP(n_neighbors=10, min_dist=0.01, random_state=42).fit_transform(
        data, labels
    )
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.97,
        "Insufficiently trustworthy embedding for" "blobs dataset: {}".format(trust),
    )


def test_semisupervised_umap_trustworthiness():
    data, labels = datasets.make_blobs(50, cluster_std=0.5, random_state=42)
    labels[10:30] = -1
    embedding = UMAP(n_neighbors=10, min_dist=0.01, random_state=42).fit_transform(
        data, labels
    )
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.97,
        "Insufficiently trustworthy embedding for" "blobs dataset: {}".format(trust),
    )


def test_metric_supervised_umap_trustworthiness():
    data, labels = datasets.make_blobs(50, cluster_std=0.5, random_state=42)
    embedding = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        target_metric="l1",
        target_weight=0.8,
        n_epochs=100,
        random_state=42,
    ).fit_transform(data, labels)
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.95,
        "Insufficiently trustworthy embedding for" "blobs dataset: {}".format(trust),
    )


def test_string_metric_supervised_umap_trustworthiness():
    data, labels = datasets.make_blobs(50, cluster_std=0.5, random_state=42)
    labels = np.array(["this", "that", "other"])[labels]
    embedding = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        target_metric="string",
        target_weight=0.8,
        n_epochs=100,
        random_state=42,
    ).fit_transform(data, labels)
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.95,
        "Insufficiently trustworthy embedding for" "blobs dataset: {}".format(trust),
    )


def test_discrete_metric_supervised_umap_trustworthiness():
    data, labels = datasets.make_blobs(50, cluster_std=0.5, random_state=42)
    embedding = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        target_metric="ordinal",
        target_weight=0.8,
        n_epochs=100,
        random_state=42,
    ).fit_transform(data, labels)
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.95,
        "Insufficiently trustworthy embedding for" "blobs dataset: {}".format(trust),
    )


def test_count_metric_supervised_umap_trustworthiness():
    data, labels = datasets.make_blobs(50, cluster_std=0.5, random_state=42)
    labels = (labels ** 2) + 2 * labels
    embedding = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        target_metric="count",
        target_weight=0.8,
        n_epochs=100,
        random_state=42,
    ).fit_transform(data, labels)
    trust = trustworthiness(data, embedding, 10)
    assert_greater_equal(
        trust,
        0.95,
        "Insufficiently trustworthy embedding for" "blobs dataset: {}".format(trust),
    )


def test_umap_trustworthiness_on_iris():
    embedding = iris_model.embedding_
    trust = trustworthiness(iris.data, embedding, 10)
    assert_greater_equal(
        trust,
        0.97,
        "Insufficiently trustworthy embedding for" "iris dataset: {}".format(trust),
    )


def test_initialized_umap_trustworthiness_on_iris():
    data = iris.data
    embedding = UMAP(
        n_neighbors=10, min_dist=0.01, init=data[:, 2:], n_epochs=200, random_state=42
    ).fit_transform(data)
    trust = trustworthiness(iris.data, embedding, 10)
    assert_greater_equal(
        trust,
        0.97,
        "Insufficiently trustworthy embedding for" "iris dataset: {}".format(trust),
    )


def test_umap_transform_on_iris():
    data = iris.data[iris_selection]
    fitter = UMAP(n_neighbors=10, min_dist=0.01, n_epochs=200, random_state=42).fit(
        data
    )

    new_data = iris.data[~iris_selection]
    embedding = fitter.transform(new_data)

    trust = trustworthiness(new_data, embedding, 10)
    assert_greater_equal(
        trust,
        0.85,
        "Insufficiently trustworthy transform for" "iris dataset: {}".format(trust),
    )


def test_umap_sparse_transform_on_iris():
    data = sparse.csr_matrix(iris.data[iris_selection])
    assert sparse.issparse(data)
    fitter = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        random_state=42,
        n_epochs=100,
        force_approximation_algorithm=True,
    ).fit(data)

    new_data = sparse.csr_matrix(iris.data[~iris_selection])
    assert sparse.issparse(new_data)
    embedding = fitter.transform(new_data)

    trust = trustworthiness(new_data, embedding, 10)
    assert_greater_equal(
        trust,
        0.80,
        "Insufficiently trustworthy transform for" "iris dataset: {}".format(trust),
    )


def test_umap_transform_on_iris_modified_dtype():
    data = iris.data[iris_selection]
    fitter = UMAP(n_neighbors=10, min_dist=0.01, random_state=42).fit(data)
    fitter.embedding_ = fitter.embedding_.astype(np.float64)

    new_data = iris.data[~iris_selection]
    embedding = fitter.transform(new_data)

    trust = trustworthiness(new_data, embedding, 10)
    assert_greater_equal(
        trust,
        0.89,
        "Insufficiently trustworthy transform for" "iris dataset: {}".format(trust),
    )


def test_umap_trustworthiness_on_sphere_iris():
    data = iris.data
    embedding = UMAP(
        n_neighbors=10,
        min_dist=0.01,
        n_epochs=200,
        random_state=42,
        output_metric="haversine",
    ).fit_transform(data)
    # Since trustworthiness doesn't support haversine, project onto
    # a 3D embedding of the sphere and use cosine distance
    r = 3
    projected_embedding = np.vstack(
        [
            r * np.sin(embedding[:, 0]) * np.cos(embedding[:, 1]),
            r * np.sin(embedding[:, 0]) * np.sin(embedding[:, 1]),
            r * np.cos(embedding[:, 0]),
        ]
    ).T
    trust = trustworthiness(iris.data, projected_embedding, 10, metric="cosine")
    assert_greater_equal(
        trust,
        0.80,
        "Insufficiently trustworthy spherical embedding for iris dataset: {}".format(
            trust
        ),
    )


def test_umap_clusterability_on_supervised_iris():
    embedding = supervised_iris_model.embedding_
    clusters = KMeans(3).fit_predict(embedding)
    assert_greater_equal(adjusted_rand_score(clusters, iris.target), 0.95)


# # This test is currently to expensive to run when turning
# # off numba JITting to detect coverage.
# @SkipTest
# def test_umap_regression_supervision(): # pragma: no cover
#     boston = datasets.load_boston()
#     data = boston.data
#     embedding = UMAP(n_neighbors=10,
#                      min_dist=0.01,
#                      target_metric='euclidean',
#                      random_state=42).fit_transform(data, boston.target)


def test_umap_inverse_transform_on_iris():
    highd_tree = KDTree(iris.data)
    fitter = iris_model
    lowd_tree = KDTree(fitter.embedding_)
    for i in range(1, 150, 20):
        query_point = fitter.embedding_[i]
        near_points = lowd_tree.query([query_point], k=5, return_distance=False)
        centroid = np.mean(np.squeeze(fitter.embedding_[near_points]), axis=0)
        highd_centroid = fitter.inverse_transform([centroid])
        highd_near_points = highd_tree.query(
            highd_centroid, k=10, return_distance=False
        )
        assert_greater_equal(
            np.intersect1d(near_points, highd_near_points[0]).shape[0], 3
        )


def test_blobs_cluster():
    data, labels = datasets.make_blobs(n_samples=500, n_features=10, centers=5)
    embedding = UMAP().fit_transform(data)
    assert_equal(adjusted_rand_score(labels, KMeans(5).fit_predict(embedding)), 1.0)


def test_multi_component_layout():
    data, labels = datasets.make_blobs(
        100, 2, centers=5, cluster_std=0.5, center_box=[-20, 20], random_state=42
    )

    true_centroids = np.empty((labels.max() + 1, data.shape[1]), dtype=np.float64)

    for label in range(labels.max() + 1):
        true_centroids[label] = data[labels == label].mean(axis=0)

    true_centroids = normalize(true_centroids, norm="l2")

    embedding = UMAP(n_neighbors=4).fit_transform(data)
    embed_centroids = np.empty((labels.max() + 1, data.shape[1]), dtype=np.float64)
    embed_labels = KMeans(n_clusters=5).fit_predict(embedding)

    for label in range(embed_labels.max() + 1):
        embed_centroids[label] = data[embed_labels == label].mean(axis=0)

    embed_centroids = normalize(embed_centroids, norm="l2")

    error = np.sum((true_centroids - embed_centroids) ** 2)

    assert_less(error, 15.0, msg="Multi component embedding to far astray")


def test_negative_op():
    u = UMAP(set_op_mix_ratio=-1.0)
    assert_raises(ValueError, u.fit, nn_data)


def test_too_large_op():
    u = UMAP(set_op_mix_ratio=1.5)
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_too_large_min_dist():
    u = UMAP(min_dist=2.0)
    # a RuntimeWarning about division by zero in a,b curve fitting is expected
    # caught and ignored for this test
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        assert_raises(ValueError, u.fit, nn_data)


def test_negative_min_dist():
    u = UMAP(min_dist=-1)
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_ncomponents():
    u = UMAP(n_components=-1)
    assert_raises(ValueError, u.fit, nn_data)


def test_non_integer_ncomponents():
    u = UMAP(n_components=1.5)
    assert_raises(ValueError, u.fit, nn_data)


def test_too_small_nneighbors():
    u = UMAP(n_neighbors=0.5)
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_nneighbors():
    u = UMAP(n_neighbors=-1)
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_metric():
    u = UMAP(metric=45)
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_learning_rate():
    u = UMAP(learning_rate=-1.5)
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_repulsion():
    u = UMAP(repulsion_strength=-0.5)
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_sample_rate():
    u = UMAP(negative_sample_rate=-1)
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_init():
    u = UMAP(init="foobar")
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_numeric_init():
    u = UMAP(init=42)
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_matrix_init():
    u = UMAP(init=np.array([[0, 0, 0], [0, 0, 0]]))
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_nepochs():
    u = UMAP(n_epochs=-2)
    assert_raises(ValueError, u.fit, nn_data)


def test_negative_target_nneighbors():
    u = UMAP(target_n_neighbors=1)
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_output_metric():
    u = UMAP(output_metric="foobar")
    assert_raises(ValueError, u.fit, nn_data)
    u = UMAP(output_metric="precomputed")
    assert_raises(ValueError, u.fit, nn_data)
    u = UMAP(output_metric="hamming")
    assert_raises(ValueError, u.fit, nn_data)


def test_haversine_on_highd():
    u = UMAP(metric="haversine")
    assert_raises(ValueError, u.fit, nn_data)


def test_haversine_embed_to_highd():
    u = UMAP(n_components=3, output_metric="haversine")
    assert_raises(ValueError, u.fit, nn_data)


def test_bad_transform_data():
    u = UMAP().fit([[1, 1, 1, 1]])
    assert_raises(ValueError, u.transform, [[0, 0, 0, 0]])


def test_umap_bad_nn():
    assert_raises(ValueError, nearest_neighbors, nn_data, 10, 42, {}, False, np.random)


def test_umap_bad_nn_sparse():
    assert_raises(
        ValueError,
        nearest_neighbors,
        sparse_nn_data,
        10,
        "seuclidean",
        {},
        False,
        np.random,
    )


def test_too_many_neighbors_warns():
    u = UMAP(a=1.2, b=1.75, n_neighbors=2000, n_epochs=11, init="random")
    u.fit(
        nn_data[:100,]
    )
    assert_equal(u._a, 1.2)
    assert_equal(u._b, 1.75)


def test_umap_fit_params():
    # x and y are required to be the same length
    u = UMAP()
    x = np.random.uniform(0, 1, (256, 10))
    y = np.random.randint(10, size=(257,))
    assert_raises(ValueError, u.fit, x, y)

    u = UMAP()
    x = np.random.uniform(0, 1, (256, 10))
    y = np.random.randint(10, size=(255,))
    assert_raises(ValueError, u.fit, x, y)

    u = UMAP()
    x = np.random.uniform(0, 1, (256, 10))
    assert_raises(ValueError, u.fit, x, [])

    u = UMAP()
    x = np.random.uniform(0, 1, (256, 10))
    y = np.random.randint(10, size=(256,))
    res = u.fit(x, y)
    assert isinstance(res, UMAP)

    u = UMAP()
    x = np.random.uniform(0, 1, (256, 10))
    res = u.fit(x)
    assert isinstance(res, UMAP)


def test_umap_transform_embedding_stability():
    """Test that transforming data does not alter the learned embeddings

    Issue #217 describes how using transform to embed new data using a
    trained UMAP transformer causes the fitting embedding matrix to change
    in cases when the new data has the same number of rows as the original
    training data.
    """

    data = iris.data[iris_selection]
    fitter = UMAP(n_neighbors=10, min_dist=0.01, random_state=42).fit(data)
    original_embedding = fitter.embedding_.copy()

    # The important point is that the new data has the same number of rows
    # as the original fit data
    new_data = np.random.random(data.shape)
    embedding = fitter.transform(new_data)

    assert_array_equal(
        original_embedding,
        fitter.embedding_,
        "Transforming new data changed the original embeddings",
    )

    # Example from issue #217
    a = np.random.random((1000, 10))
    b = np.random.random((1000, 5))

    umap = UMAP()
    u1 = umap.fit_transform(a[:, :5])
    u1_orig = u1.copy()
    assert_array_equal(u1_orig, umap.embedding_)

    u2 = umap.transform(b)
    assert_array_equal(u1_orig, umap.embedding_)


def test_dataframe_umap_bad_params():
    u = DataFrameUMAP(
        metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], set_op_mix_ratio=-1.0
    )
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(
        metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], set_op_mix_ratio=1.5
    )
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], min_dist=2.0)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], min_dist=-1)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], n_components=-1)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], n_components=1.5)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], n_neighbors=0.5)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], n_neighbors=-1)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "foobar", [0, 1, 2, 3, 4])])
    assert_raises(AssertionError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], learning_rate=-1.5)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(
        metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], repulsion_strength=-0.5
    )
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(
        metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], negative_sample_rate=-1
    )
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], init="foobar")
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], init=42)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(
        metrics=[("e", "euclidean", [0, 1, 2, 3, 4])],
        init=np.array([[0, 0, 0], [0, 0, 0]]),
    )
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], n_epochs=-2)
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(
        metrics=[("e", "euclidean", [0, 1, 2, 3, 4])], target_n_neighbors=1
    )
    assert_raises(ValueError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", "bad_columns")])
    assert_raises(AssertionError, u.fit, nn_data)
    u = DataFrameUMAP(metrics=[("e", "euclidean", [0.1, 0.2, 0.75])])
    assert_raises(AssertionError, u.fit, nn_data)

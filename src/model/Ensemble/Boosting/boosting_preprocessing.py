import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from course_lib.Base.BaseRecommender import BaseRecommender
from src.utils.general_utility_functions import get_total_number_of_users, get_total_number_of_items
from sklearn.preprocessing import MinMaxScaler


def preprocess_dataframe_after_reading(df: pd.DataFrame):
    df = df.copy()
    df = df.drop(columns=["index"], inplace=False)
    df = df.sort_values(by="user_id", ascending=True)
    df = df.reset_index()
    df = df.drop(columns=["index"], inplace=False)
    return df


def get_dataframe(user_id_array, remove_seen_flag, cutoff, main_recommender, path, mapper, recommender_list,
                  URM_train):
    # Get dataframe for these users
    data_frame = get_boosting_base_dataframe(user_id_array=user_id_array, exclude_seen=remove_seen_flag,
                                             cutoff=cutoff, top_recommender=main_recommender)
    for rec in recommender_list:
        data_frame = add_recommender_predictions(data_frame=data_frame, recommender=rec,
                                                 cutoff=cutoff, column_name=rec.RECOMMENDER_NAME)

    data_frame = add_ICM_information(data_frame=data_frame, path=path)
    data_frame = add_UCM_information(data_frame=data_frame, path=path, user_mapper=mapper)
    data_frame = add_user_len_information(data_frame=data_frame, URM_train=URM_train)

    data_frame = data_frame.sort_values(by="user_id", ascending=True)
    data_frame = data_frame.reset_index()
    data_frame.drop(columns=["index"], inplace=False)

    return data_frame


def add_item_popularity(data_frame: pd.DataFrame, URM_train: csr_matrix):
    """
    Add the item popularity to the dataframe

    :param data_frame: data frame containing information for boosting
    :param URM_train: URM train matrix
    :return: dataframe containing boosting information + item popularity
    """
    print("Adding item popularity", end="")
    data_frame = data_frame.copy()

    pop_items = (URM_train > 0).sum(axis=0)
    pop_items = np.array(pop_items).squeeze()
    item_ids = np.arange(URM_train.shape[1])
    data = np.array([item_ids, pop_items])
    data = np.transpose(data)

    new_df = pd.DataFrame(data=data, columns=["row", "item_pop"])

    data_frame = pd.merge(data_frame, new_df, left_on="item_id", right_on="row")
    data_frame = data_frame.drop(columns=["row"], inplace=False)

    print("Done")

    return data_frame


def add_label(data_frame: pd.DataFrame, URM_train: csr_matrix):
    """
    Create a dataframe with a single column with the correct predictions

    :param data_frame: data frame containing information for boosting
    :param URM_train: URM train matrix
    :return: numpy array containing y information
    """
    print("Retrieving training labels")
    user_ids = data_frame['user_id'].values
    item_ids = data_frame['item_id'].values

    y = np.zeros(user_ids.size)

    for i in range(0, user_ids.size):
        if i % 5000 == 0:
            print("{} done over {}".format(i, user_ids.size))
        true_ratings = URM_train[user_ids[i]].indices
        if item_ids[i] in true_ratings:
            y[i] = 1
        else:
            y[i] = 0

    non_zero_count = np.count_nonzero(y)
    print("There are {} non-zero ratings in {}".format(non_zero_count, y.size))

    return y, non_zero_count, y.size


def add_user_len_information(data_frame: pd.DataFrame, URM_train: csr_matrix):
    """
    Add information concerning the user profile length to the row of the dataframe

    :param data_frame: data frame that is being pre-processed from boosting
    :param URM_train: URM train from which to take profile length information
    :return: data frame with new content inserted
    """
    print("Adding user profile length")
    data_frame = data_frame.copy()

    user_act = (URM_train > 0).sum(axis=1)
    user_act = np.array(user_act).squeeze()
    user_ids = np.arange(URM_train.shape[0])
    data = np.array([user_ids, user_act])
    data = np.transpose(data)
    new_df = pd.DataFrame(data=data, columns=["row", "user_act"])

    data_frame = pd.merge(data_frame, new_df, left_on="user_id", right_on="row")
    data_frame = data_frame.drop(columns=["row"], inplace=False)

    return data_frame


def remap_data_frame(df: pd.DataFrame, mapper):
    """
    Change user_id columns of the df given in input, according to the mapper.
    Users that are not present will be removed, and the others will be mapped to the correct number.


    :param df: dataframe that will be modified
    :param mapper: mapper according to which the dataframe will be modified
    :return: dataframe with "user_id" column modified properly
    """
    df = df.copy()

    # Remove users that are not present in the mapper
    original_users = df['row'].values
    new_users_key = list(mapper.keys())
    new_users_key = list(map(int, new_users_key))
    new_users_key = np.array(new_users_key)
    mask = np.in1d(original_users, new_users_key, invert=True)
    remove = original_users[mask]
    df = df.set_index("row")
    mask = np.in1d(df.index, remove)
    df = df.drop(df.index[mask])

    # Map the index to the new one
    df = df.reset_index()
    df['row'] = df['row'].map(lambda x: mapper[str(x)])

    return df


def add_UCM_information(data_frame: pd.DataFrame, user_mapper, path="../../data/", use_region=True, use_age=True):
    """
    Add UCM information to the data frame for XGboost

    :param data_frame: data frame containing information being pre-processed for boosting
    :param user_mapper: mapper original users to train users
    :param path: where to read UCM csv files
    :param use_region: True is region information should be used, false otherwise
    :param use_age: True if age information should be used, false otherwise
    :return: pd.DataFrame containing the original data frame+ UCM information
    """
    print("Add UCM information")
    t_users = get_total_number_of_users()  # Total number of users (-1 since indexing from 0)

    data_frame = data_frame.copy()
    df_region: pd.DataFrame = pd.read_csv(path + "data_UCM_region.csv")
    df_age: pd.DataFrame = pd.read_csv(path + "data_UCM_age.csv")

    # Re-map UCM data frame in order to have the correct user information
    if use_region:
        df_region = df_region[['row', 'col']]

        dfDummies = pd.get_dummies(df_region['col'], prefix='region')
        dfDummies = dfDummies.join(df_region['row'])
        dfDummies = dfDummies.groupby(['row'], as_index=False).sum()

        # Fill missing values
        user_present = dfDummies['row'].values
        total_users = np.arange(t_users)
        mask = np.in1d(total_users, user_present, invert=True)
        missing_users = total_users[mask]
        num_col = dfDummies.columns.size
        missing_val = np.zeros(shape=(num_col, missing_users.size))
        missing_val[0] = missing_users
        missing_df = pd.DataFrame(data=np.transpose(missing_val), dtype=np.int32, columns=dfDummies.columns)
        df_region = dfDummies.append(missing_df)

        if user_mapper is not None:
            df_region = remap_data_frame(df=df_region, mapper=user_mapper)
        data_frame = pd.merge(data_frame, df_region, right_on="row", left_on="user_id")
        data_frame = data_frame.drop(columns=["row"], inplace=False)
    if use_age:
        df_age = df_age[['row', 'col']]

        # Handle missing values: fill with mode + 1
        users_present = df_age['row'].values
        total_users = np.arange(t_users)
        mask = np.in1d(total_users, users_present, invert=True)
        missing_users = total_users[mask].astype(np.int32)
        missing_val_filled = np.ones(missing_users.size) * (int(df_age['col'].mode()) + 1)
        missing = np.array([missing_users, missing_val_filled], dtype=np.int32)
        missing_df = pd.DataFrame(data=np.transpose(missing), columns=["row", "col"])
        df_age = df_age.append(missing_df)
        df_age = df_age.reset_index()
        df_age = df_age[['row', 'col']]

        if user_mapper is not None:
            df_age = remap_data_frame(df=df_age, mapper=user_mapper)
        df_age = df_age.rename(columns={"col": "age"})
        data_frame = pd.merge(data_frame, df_age, right_on="row", left_on="user_id")
        data_frame = data_frame.drop(columns=["row"], inplace=False)

    return data_frame


def add_ICM_information(data_frame: pd.DataFrame, path="../../data/", use_price=True, use_asset=True,
                        use_subclass=True):
    """
    Add information form the ICM files to the data frame

    :param data_frame: data frame that is being pre-processed for boosting
    :param path: path to the folder containing the csv files
    :param use_price: True if you wish to append price information, false otherwise
    :param use_asset: True if you wish to append asset information, false otherwise
    :param use_subclass: True if you wish to append subclass information, false otherwise
    :return: pd.DataFrame containing the information
    """
    print("Adding ICM information")
    data_frame = data_frame.copy()
    df_price: pd.DataFrame = pd.read_csv(path + "data_ICM_price.csv")
    df_asset: pd.DataFrame = pd.read_csv(path + "data_ICM_asset.csv")
    df_subclass: pd.DataFrame = pd.read_csv(path + "data_ICM_sub_class.csv")

    total_items = get_total_number_of_items()
    total_items = np.arange(total_items)

    if use_price:
        # Handle missing values
        item_present = df_price['row'].values
        mask = np.in1d(total_items, item_present, invert=True)
        missing_items = total_items[mask].astype(np.int32)
        missing_val_filled = np.ones(missing_items.size) * df_price['data'].median()
        missing = np.array([missing_items, missing_val_filled])
        missing_df = pd.DataFrame(data=np.transpose(missing), columns=['row', 'data'])
        df_price = df_price.append(missing_df)
        df_price = df_price.reset_index()
        df_price = df_price[['row', 'data']]

        df_price = df_price.rename(columns={"data": "price"})
        data_frame = pd.merge(data_frame, df_price, right_on="row", left_on="item_id")
        data_frame = data_frame.drop(columns=['row'], inplace=False)
    if use_asset:
        # Handle missing values
        item_present = df_asset['row'].values
        mask = np.in1d(total_items, item_present, invert=True)
        missing_items = total_items[mask].astype(np.int32)
        missing_val_filled = np.ones(missing_items.size) * df_asset['data'].median()
        missing = np.array([missing_items, missing_val_filled])
        missing_df = pd.DataFrame(data=np.transpose(missing), columns=['row', 'data'])
        df_asset = df_asset.append(missing_df)
        df_asset = df_asset.reset_index()
        df_asset = df_asset[['row', 'data']]

        df_asset = df_asset.rename(columns={"data": "asset"})
        data_frame = pd.merge(data_frame, df_asset, right_on="row", left_on="item_id")
        data_frame = data_frame.drop(columns=["row"], inplace=False)
    if use_subclass:
        df_subclass = df_subclass[['row', 'col']]
        df_subclass = df_subclass.rename(columns={"col": "subclass"})
        data_frame = pd.merge(data_frame, df_subclass, right_on="row", left_on="item_id")
        data_frame = data_frame.drop(columns=["row"], inplace=False)

    return data_frame


def add_recommender_predictions(data_frame: pd.DataFrame, recommender: BaseRecommender, cutoff: int,
                                column_name: str, min_max_scaling=True):
    new_df = data_frame.copy()
    items = new_df['item_id'].values.astype(int)
    users = new_df['user_id'].values.astype(int)

    print("Add recommender predictions - COLUMN NAME: " + str(column_name))
    new_df[column_name] = 0

    for i, user_id in enumerate(np.unique(users)):
        if i % 10000 == 0:
            print("{} done over {}".format(i, np.unique(users).size))
        items_for_user_id = items[(i * cutoff):(i * cutoff) + cutoff]
        if items_for_user_id.size != np.unique(items_for_user_id).size:
            raise RuntimeError("These two arrays should have the same size")

        scores = recommender._compute_item_score([user_id]).squeeze()[items_for_user_id]
        if scores.size != items_for_user_id.size:
            raise RuntimeError("These two arrays should have the same size")

        new_df.loc[new_df['user_id'] == user_id, [column_name]] = scores.reshape(scores.size, 1)

    if min_max_scaling:
        values: np.array = new_df[column_name].values
        scaler = MinMaxScaler()
        scaler.fit(values.reshape(-1, 1))
        new_values = scaler.transform(values.reshape(-1, 1))
        new_df[column_name] = new_values

    return new_df


def get_boosting_base_dataframe(user_id_array, top_recommender: BaseRecommender, cutoff: int,
                                exclude_seen=False):
    """
    Get boosting data-frame preprocessed.
    In particular, it will create a data frame containing "user_id" presents in user_id_array, and computing
    possible recommendations using top_recommender, from which "item_id" will be extracted

    :param exclude_seen:
    :param user_id_array: user that you want to recommend
    :param top_recommender: top recommender used for building the dataframe
    :param cutoff: if you are interested in MAP@10, choose a large number, for instance, 20
    :return: dataframe containing the described information
    """
    print("Retrieving base dataframe using the main recommender...")
    # Setting items
    if exclude_seen:
        recommendations = np.array(top_recommender.recommend(user_id_array=user_id_array, cutoff=cutoff,
                                                             remove_seen_flag=exclude_seen))
    else:
        # Generate recommendations
        double_rec_false = np.array(top_recommender.recommend(user_id_array=user_id_array, cutoff=cutoff * 2,
                                                              remove_seen_flag=False))
        rec_true = np.array(top_recommender.recommend(user_id_array=user_id_array, cutoff=cutoff,
                                                      remove_seen_flag=True))

        # Get rid of common recommendations
        mask = [np.isin(double_rec_false[i], rec_true[i], invert=True) for i in range(double_rec_false.shape[0])]
        recommendations = np.zeros(shape=rec_true.shape)
        for i in range(recommendations.shape[0]):
            recommendations[i] = double_rec_false[i][mask[i]][0:cutoff]

    user_recommendations_items = recommendations.reshape((recommendations.size, 1)).squeeze()

    # Setting users
    user_recommendations_user_id = np.zeros(user_recommendations_items.size)
    for i, user in enumerate(user_id_array):
        if user % 10000 == 0:
            print("{} done over {}".format(i, user_id_array.size))
        user_recommendations_user_id[(i * cutoff):(i * cutoff) + cutoff] = user

    data_frame = pd.DataFrame({"user_id": user_recommendations_user_id, "item_id": user_recommendations_items})

    return data_frame
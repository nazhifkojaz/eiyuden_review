import os
import pandas as pd
import pytest
from scripts.SteamReviewCollector import SteamReviewCollector

@pytest.fixture
def collector():
    return SteamReviewCollector()

def test_fetch_reviews(mocker, collector):
    # Mock the requests.get method
    mock_response = mocker.patch('requests.get')
    mock_response.return_value.status_code = 200
    mock_response.return_value.json.return_value = {
        "reviews": [],
        "cursor": "next_cursor_value"  # mock cursor pagination
    }

    response = collector.fetch_reviews()
    assert response is not None
    assert response['cursor'] == "next_cursor_value"

def test_process_reviews(collector):
    sample_response = {
        "reviews": [
            {"recommendationid": 1, "review": "Great game!", "timestamp_created": 1234567890},
        ]
    }
    processed_reviews = collector.process_reviews(sample_response)
    assert len(processed_reviews) == 1
    assert processed_reviews[0]['review'] == "Great game!"

def test_save_to_csv(mocker, collector):
    # Mock os.path.exists and os.rename
    mocker.patch('os.path.exists', side_effect=lambda x: x == 'data/reviews_latest.csv')
    mock_rename = mocker.patch('os.rename')
    mock_to_csv = mocker.patch('pandas.DataFrame.to_csv')

    collector.collected_data = pd.DataFrame({'review': ['Great game!']})
    
    collector.save_to_csv()

    # check if the methods were called
    mock_to_csv.assert_called_once_with('data/reviews_latest.csv', index=False)
    mock_rename.assert_called_once()

def test_manage_old_reviews(mocker, collector):
    # list of the mock files
    mock_listdir = mocker.patch('os.listdir', return_value=[
        'reviews_old_2024-10-01.csv',
        'reviews_old_2024-09-01.csv',
        'reviews_old_2024-08-01.csv',
        'reviews_old_2024-07-01.csv',
        'reviews_old_2024-06-01.csv',
    ])
    
    # Mock the modification times
    mock_getmtime = mocker.patch('os.path.getmtime', side_effect=[
        5,  # reviews_old_2024-10-01.csv
        4,  # reviews_old_2024-09-01.csv
        3,  # reviews_old_2024-08-01.csv
        2,  # reviews_old_2024-07-01.csv
        1,  # reviews_old_2024-06-01.csv
    ])

    # Mock os.remove
    mock_remove = mocker.patch('os.remove')

    collector.manage_old_reviews("dummy_directory")

    # should have been called 2 times
    assert mock_remove.call_count == 2

    # get the list of removed files
    removed_files = [call[0][0] for call in mock_remove.call_args_list]

    # check the deleted files
    assert 'dummy_directory\\reviews_old_2024-06-01.csv' in removed_files  # deleted
    assert 'dummy_directory\\reviews_old_2024-07-01.csv' in removed_files  # deleted
    assert 'dummy_directory\\reviews_old_2024-08-01.csv' not in removed_files  # not deleted
    assert 'dummy_directory\\reviews_old_2024-09-01.csv' not in removed_files  # not deleted
    assert 'dummy_directory\\reviews_old_2024-10-01.csv' not in removed_files  # not deleted

def test_run(mocker, collector):
    # Mock fetch_reviews and process_reviews
    mock_fetch = mocker.patch.object(collector, 'fetch_reviews', return_value={
        "reviews": [{"recommendationid": 1, "review": "Great game!", "timestamp_created": 1234567890}],
        "cursor": "next_cursor_value"
    })
    mock_process = mocker.patch.object(collector, 'process_reviews', return_value=[
        {"recommendationid": 1, "review": "Great game!", "timestamp_created": 1234567890}
    ])
    mock_save = mocker.patch.object(collector, 'save_to_csv')

    collector.run()

    assert mock_fetch.call_count == 2 # twice, the second one went to the break
    assert mock_process.call_count == 1 # only once in the loop
    mock_save.assert_called_once()

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError

from ai_api_testing.agents.api_specs_agents.fastapi_extractor import FastAPISpecsExtractor

app = FastAPI()


class TweetScoreInput(BaseModel):
    """Tweet score input model."""

    tweet_text: str = Field(..., description="The actual text content of the tweet")
    author_followers: int = Field(..., description="Number of followers the tweet author has")
    author_following: int = Field(..., description="Number of accounts the author follows")
    author_verified: bool = Field(default=False, description="Whether the author is verified")
    tweet_has_media: bool = Field(default=False, description="Whether the tweet contains media (images/videos)")
    tweet_has_links: bool = Field(default=False, description="Whether the tweet contains URLs")
    tweet_has_hashtags: bool = Field(default=False, description="Whether the tweet contains hashtags")
    tweet_reply_count: int = Field(default=0, description="Number of replies to this tweet")
    tweet_retweet_count: int = Field(default=0, description="Number of retweets")
    tweet_like_count: int = Field(default=0, description="Number of likes")
    tweet_quote_count: int = Field(default=0, description="Number of quote tweets")


@app.post("/predict")
async def predict(tweet_data: TweetScoreInput):
    """Predict tweet score."""
    engagement_score = 0.75
    visibility_score = 0.85

    return {
        "prediction": {
            "engagement_score": engagement_score,
            "visibility_score": visibility_score,
            "recommendation": "high_visibility" if visibility_score > 0.8 else "normal",
        }
    }


client = TestClient(app)


def test_predict_endpoint():
    """Test the predict endpoint."""
    response = client.post(
        "/predict",
        content=TweetScoreInput(
            tweet_text="Hello, world!",
            author_followers=100,
            author_following=50,
            author_verified=False,
            tweet_has_media=False,
            tweet_has_links=False,
            tweet_has_hashtags=False,
            tweet_reply_count=0,
            tweet_retweet_count=0,
            tweet_like_count=0,
            tweet_quote_count=0,
        ).model_dump_json(),
    )

    assert response.status_code == 200
    assert "prediction" in response.json()


def test_predict_endpoint_missing_fields():
    """Test the predict endpoint with missing fields."""
    with pytest.raises(ValidationError) as exc_info:
        client.post(
            "/predict",
            content=TweetScoreInput(
                tweet_text="Hello, world!",
            ).model_dump_json(),
        )

    assert exc_info.value.errors()[0]["loc"] == ("author_followers",)


def test_discover_endpoint_response():
    """Test the discover endpoint response."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_spec = response.json()
    assert openapi_spec["openapi"] == "3.1.0"
    assert openapi_spec["info"]["title"] == "FastAPI"
    assert "/predict" in openapi_spec["paths"]

    predict_path = openapi_spec["paths"]["/predict"]
    assert "post" in predict_path

    # Get the request body schema reference and extract the actual schema
    request_schema_ref = predict_path["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    schema_name = request_schema_ref.split("/")[-1]
    request_schema = openapi_spec["components"]["schemas"][schema_name]

    assert "properties" in request_schema
    assert "tweet_text" in request_schema["properties"]
    assert "author_followers" in request_schema["properties"]


def test_discover_endpoint_response_schema():
    """Test the discover endpoint response schema."""
    agent = FastAPISpecsExtractor()
    endpoints = agent.extract_specs(app=app)

    assert len(endpoints) == 1
    assert endpoints[0].request_body is not None
    assert endpoints[0].response_schema is not None

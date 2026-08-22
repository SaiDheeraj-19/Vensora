import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.registry import Base
from app.modules.agents.models import Agent
from app.modules.campaigns.models import Campaign, CampaignStatus, CampaignType
from app.modules.contacts.models import Contact
from app.modules.calls.models import Call

@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_telephony_models_creation(db_session):
    agent = Agent(
        name="Sales Assistant",
        system_prompt="You are a helpful sales assistant.",
        voice_id="voice-xyz",
        provider="elevenlabs"
    )
    db_session.add(agent)
    db_session.flush()
    
    campaign = Campaign(
        name="Outbound Lead Gen",
        agent_id=agent.id,
        campaign_type=CampaignType.OUTBOUND,
        status=CampaignStatus.RUNNING
    )
    db_session.add(campaign)
    db_session.flush()
    
    contact = Contact(
        phone_number="+15550100",
        first_name="John",
        last_name="Doe",
        contact_metadata={"source": "website"}
    )
    db_session.add(contact)
    db_session.flush()
    
    call = Call(
        twilio_call_sid="CA1234567890",
        campaign_id=campaign.id,
        contact_id=contact.id,
        status="completed",
        duration_seconds=120,
        recording_url="minio://recordings/123.wav"
    )
    db_session.add(call)
    db_session.flush()
    
    db_session.commit()
    
    assert agent.id is not None
    assert campaign.agent.id == agent.id
    assert call.campaign.id == campaign.id
    assert call.contact.id == contact.id
    assert len(agent.campaigns) == 1
    assert len(campaign.calls) == 1

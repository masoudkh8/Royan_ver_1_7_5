"""
Seed script for Exhibition and Trading modules
Creates sample data for testing
"""
from app import create_app
from extensions import db
from datetime import datetime, timedelta
import uuid

def seed_data():
    app = create_app()
    with app.app_context():
        from models.exhibition import Exhibition, Booth, ExhibitionStatus, BoothType
        from models.trading import TradingPair
        
        # Create sample exhibition
        if Exhibition.query.count() == 0:
            active_status = ExhibitionStatus.query.filter_by(status='active').first()
            
            exhibition = Exhibition(
                title_fa='Metisma International Exhibition',
                title_en='Metisma International Exhibition',
                description_fa='Virtual business exhibition',
                description_en='The largest virtual business exhibition in the Middle East',
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                status_id=active_status.id if active_status else 3,
                has_virtual_tour=True,
                has_3d_booths=True
            )
            db.session.add(exhibition)
            db.session.commit()
            
            booth_types = BoothType.query.all()
            for i in range(5):
                booth = Booth(
                    exhibition_id=exhibition.id,
                    owner_type='company',
                    owner_id=uuid.uuid4(),
                    booth_number=f'B-{i+1:03d}',
                    title_fa=f'Sample Booth {i+1}',
                    title_en=f'Sample Booth {i+1}',
                    description_en=f'Description for booth number {i+1}',
                    type_id=booth_types[0].id if booth_types else 1,
                    is_active=True,
                    approval_status='approved',
                    slug=f'sample-booth-{i+1}'
                )
                db.session.add(booth)
            db.session.commit()
            print('Created 1 exhibition with 5 booths')
        
        # Create trading pairs
        if TradingPair.query.count() == 0:
            pairs = [
                ('BTC', 'USDT', 'BTC/USDT'),
                ('ETH', 'USDT', 'ETH/USDT'),
                ('GOLD', 'USD', 'GOLD/USD'),
            ]
            for base, quote, symbol in pairs:
                pair = TradingPair(
                    base_asset=base,
                    quote_asset=quote,
                    symbol=symbol,
                    min_order_size=0.001,
                    max_order_size=100,
                    is_active=True
                )
                db.session.add(pair)
            db.session.commit()
            print(f'Created {len(pairs)} trading pairs')
        
        print('Seed completed!')

if __name__ == '__main__':
    seed_data()

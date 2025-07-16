"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_address', sa.String(length=42), nullable=False),
        sa.Column('nft_verified', sa.Boolean(), nullable=True),
        sa.Column('nft_token_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('wallet_address', name=op.f('uq_users_wallet_address'))
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)

    # Create trades table
    op.create_table('trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trade_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('trade_type', sa.Enum('SWAP', 'BUY', 'SELL', 'LIMIT', 'STOP_LOSS', name='tradetype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'EXECUTING', 'COMPLETED', 'FAILED', 'CANCELLED', name='tradestatus'), nullable=True),
        sa.Column('token_in', sa.String(length=20), nullable=False),
        sa.Column('token_out', sa.String(length=20), nullable=False),
        sa.Column('token_in_address', sa.String(length=42), nullable=True),
        sa.Column('token_out_address', sa.String(length=42), nullable=True),
        sa.Column('amount_in', sa.Float(), nullable=False),
        sa.Column('amount_out', sa.Float(), nullable=True),
        sa.Column('estimated_amount_out', sa.Float(), nullable=True),
        sa.Column('execution_price', sa.Float(), nullable=True),
        sa.Column('slippage', sa.Float(), nullable=True),
        sa.Column('gas_estimate', sa.Integer(), nullable=True),
        sa.Column('gas_used', sa.Integer(), nullable=True),
        sa.Column('gas_price', sa.Float(), nullable=True),
        sa.Column('network', sa.String(length=20), nullable=True),
        sa.Column('transaction_hash', sa.String(length=66), nullable=True),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('original_prompt', sa.Text(), nullable=True),
        sa.Column('parsed_instruction', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('llm_provider', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dry_run', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_trades_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_trades')),
        sa.UniqueConstraint('trade_id', name=op.f('uq_trades_trade_id'))
    )
    op.create_index(op.f('ix_trades_id'), 'trades', ['id'], unique=False)
    op.create_index(op.f('ix_trades_trade_id'), 'trades', ['trade_id'], unique=True)
    op.create_index('ix_trades_user_created', 'trades', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_trades_status_created', 'trades', ['status', 'created_at'], unique=False)
    op.create_index('ix_trades_token_pair', 'trades', ['token_in', 'token_out'], unique=False)

    # Create strategies table
    op.create_table('strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'PAUSED', 'ERROR', name='strategystatus'), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('risk_limits', sa.JSON(), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('winning_trades', sa.Integer(), nullable=True),
        sa.Column('losing_trades', sa.Integer(), nullable=True),
        sa.Column('total_pnl', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_executed', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_strategies_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_strategies')),
        sa.UniqueConstraint('strategy_id', name=op.f('uq_strategies_strategy_id'))
    )
    op.create_index(op.f('ix_strategies_id'), 'strategies', ['id'], unique=False)
    op.create_index(op.f('ix_strategies_strategy_id'), 'strategies', ['strategy_id'], unique=True)

    # Create portfolios table
    op.create_table('portfolios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_value_usd', sa.Float(), nullable=True),
        sa.Column('tokens', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_portfolios_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_portfolios'))
    )
    op.create_index(op.f('ix_portfolios_id'), 'portfolios', ['id'], unique=False)
    op.create_index('ix_portfolios_user_created', 'portfolios', ['user_id', 'created_at'], unique=False)

    # Create market_data table
    op.create_table('market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('contract_address', sa.String(length=42), nullable=True),
        sa.Column('network', sa.String(length=20), nullable=True),
        sa.Column('price_usd', sa.Float(), nullable=False),
        sa.Column('price_change_24h', sa.Float(), nullable=True),
        sa.Column('volume_24h', sa.Float(), nullable=True),
        sa.Column('market_cap', sa.Float(), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_market_data')),
        sa.UniqueConstraint('symbol', 'network', name='uq_market_data_symbol_network')
    )
    op.create_index(op.f('ix_market_data_id'), 'market_data', ['id'], unique=False)
    op.create_index('ix_market_data_symbol_updated', 'market_data', ['symbol', 'updated_at'], unique=False)

    # Create system_logs table
    op.create_table('system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('trade_id', sa.String(length=50), nullable=True),
        sa.Column('additional_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_system_logs_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_system_logs'))
    )
    op.create_index(op.f('ix_system_logs_id'), 'system_logs', ['id'], unique=False)
    op.create_index('ix_system_logs_level_created', 'system_logs', ['level', 'created_at'], unique=False)
    op.create_index('ix_system_logs_category_created', 'system_logs', ['category', 'created_at'], unique=False)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('key_name', sa.String(length=100), nullable=True),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('daily_limit', sa.Integer(), nullable=True),
        sa.Column('monthly_limit', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_api_keys')),
        sa.UniqueConstraint('service_name', 'key_name', name='uq_api_keys_service_name')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    
    op.drop_index('ix_system_logs_category_created', table_name='system_logs')
    op.drop_index('ix_system_logs_level_created', table_name='system_logs')
    op.drop_index(op.f('ix_system_logs_id'), table_name='system_logs')
    op.drop_table('system_logs')
    
    op.drop_index('ix_market_data_symbol_updated', table_name='market_data')
    op.drop_index(op.f('ix_market_data_id'), table_name='market_data')
    op.drop_table('market_data')
    
    op.drop_index('ix_portfolios_user_created', table_name='portfolios')
    op.drop_index(op.f('ix_portfolios_id'), table_name='portfolios')
    op.drop_table('portfolios')
    
    op.drop_index(op.f('ix_strategies_strategy_id'), table_name='strategies')
    op.drop_index(op.f('ix_strategies_id'), table_name='strategies')
    op.drop_table('strategies')
    
    op.drop_index('ix_trades_token_pair', table_name='trades')
    op.drop_index('ix_trades_status_created', table_name='trades')
    op.drop_index('ix_trades_user_created', table_name='trades')
    op.drop_index(op.f('ix_trades_trade_id'), table_name='trades')
    op.drop_index(op.f('ix_trades_id'), table_name='trades')
    op.drop_table('trades')
    
    op.drop_index(op.f('ix_users_wallet_address'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')


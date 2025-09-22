"""
Database Management Endpoints

This module contains additional API endpoints for database management.
"""

from flask import jsonify, request
import logging
import sqlite3
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

def register_db_management_endpoints(app, db_manager, ADMIN_PASSWORD):
    """Register database management endpoints with the Flask app"""
    
    @app.route('/api/admin/check-database', methods=['POST'])
    def check_database():
        """Check database integrity and return table statistics"""
        try:
            data = request.get_json() or {}
            admin_password = data.get('admin_password')
            
            if admin_password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
            logger.info("Admin requested database integrity check")
            
            # Connect to database
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in cursor.fetchall()]
            
            # Count records in each table
            results = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                results[table] = count
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Database integrity check completed',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Database check error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/clear-wins', methods=['POST'])
    def clear_wins():
        """Clear all prize win records"""
        try:
            data = request.get_json() or {}
            admin_password = data.get('admin_password')
            
            if admin_password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
            logger.info("Admin requested to clear all win records")
            
            # Connect to database
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Count records before deletion
            cursor.execute("SELECT COUNT(*) as count FROM prize_wins")
            count_before = cursor.fetchone()['count']
            
            # Delete all records
            cursor.execute("DELETE FROM prize_wins")
            
            # Commit changes
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Cleared {count_before} win records',
                'count': count_before
            })
            
        except Exception as e:
            logger.error(f"Clear wins error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/clear-reservations', methods=['POST'])
    def clear_reservations():
        """Clear all prize reservations"""
        try:
            data = request.get_json() or {}
            admin_password = data.get('admin_password')
            
            if admin_password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
            logger.info("Admin requested to clear all reservations")
            
            # Connect to database
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Count records before deletion
            cursor.execute("SELECT COUNT(*) as count FROM prize_reservations")
            count_before = cursor.fetchone()['count']
            
            # Delete all records
            cursor.execute("DELETE FROM prize_reservations")
            
            # Commit changes
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Cleared {count_before} reservations',
                'count': count_before
            })
            
        except Exception as e:
            logger.error(f"Clear reservations error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/update-csv', methods=['POST'])
    def admin_update_csv():
        """Update the CSV configuration file"""
        try:
            data = request.get_json() or {}
            admin_password = data.get('admin_password')
            csv_content = data.get('csv_content')
            
            if admin_password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
            if not csv_content:
                return jsonify({'success': False, 'error': 'No CSV content provided'}), 400
            
            logger.info("Admin requested to update CSV configuration")
            
            # Import CSV manager
            import backend_api_csv_manager as csv_manager
            
            # Update CSV file
            result = csv_manager.update_csv_file(csv_content)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'CSV configuration updated successfully',
                    'validation_results': result.get('validation_results')
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to update CSV configuration'),
                    'validation_results': result.get('validation_results')
                }), 400
            
        except Exception as e:
            logger.error(f"Update CSV error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/admin/csv/export', methods=['POST'])
    def admin_export_csv():
        """Export the current CSV configuration"""
        try:
            data = request.get_json() or {}
            admin_password = data.get('admin_password')
            
            if admin_password != ADMIN_PASSWORD:
                return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
            logger.info("Admin requested CSV export")
            
            # Import CSV manager
            import backend_api_csv_manager as csv_manager
            
            # Get CSV content
            csv_content = csv_manager.get_csv_content()
            
            return jsonify({
                'success': True,
                'message': 'CSV exported successfully',
                'csv_content': csv_content
            })
            
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("Database management endpoints registered")
    return app

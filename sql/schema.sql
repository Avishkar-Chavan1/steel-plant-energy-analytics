-- =====================================================
-- Steel Industry Energy Consumption - Database Schema
-- =====================================================

CREATE DATABASE IF NOT EXISTS steel_energy;
USE steel_energy;

DROP TABLE IF EXISTS cleaned_energy;
CREATE TABLE cleaned_energy (
    id                              INT AUTO_INCREMENT PRIMARY KEY,
    record_datetime                 DATETIME,
    day_of_week                     VARCHAR(10),
    week_status                     VARCHAR(10),
    nsm                             INT,
    load_type                       VARCHAR(20),
    usage_kwh                       DECIMAL(10,4),
    lagging_reactive_power_kvarh    DECIMAL(10,4),
    leading_reactive_power_kvarh    DECIMAL(10,4),
    co2_tco2                        DECIMAL(10,6),
    lagging_power_factor            DECIMAL(6,3),
    leading_power_factor            DECIMAL(6,3),
    hour_of_day                     INT,
    shift                           VARCHAR(10)
);

-- Load the cleaned CSV (adjust path):
-- LOAD DATA LOCAL INFILE 'data/processed/cleaned_steel_energy.csv'
-- INTO TABLE cleaned_energy
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS;

-- =====================================================
-- KPI QUERIES
-- =====================================================

-- Average usage by load type
SELECT load_type, ROUND(AVG(usage_kwh),2) AS avg_usage_kwh, COUNT(*) AS records
FROM cleaned_energy
GROUP BY load_type;

-- Usage and CO2 by day of week
SELECT day_of_week,
       ROUND(SUM(usage_kwh),2) AS total_usage_kwh,
       ROUND(SUM(co2_tco2),4) AS total_co2
FROM cleaned_energy
GROUP BY day_of_week
ORDER BY FIELD(day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday');

-- Weekday vs weekend
SELECT week_status, ROUND(AVG(usage_kwh),2) AS avg_usage_kwh
FROM cleaned_energy
GROUP BY week_status;

-- Shift-wise efficiency
SELECT shift,
       ROUND(AVG(lagging_power_factor),2) AS avg_lagging_pf,
       ROUND(AVG(usage_kwh),2) AS avg_usage_kwh
FROM cleaned_energy
GROUP BY shift;

-- Top 50 highest-usage intervals
SELECT record_datetime, usage_kwh, load_type
FROM cleaned_energy
ORDER BY usage_kwh DESC
LIMIT 50;

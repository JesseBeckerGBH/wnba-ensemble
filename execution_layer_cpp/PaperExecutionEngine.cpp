#include "ExecutionInterface.hpp"
#include <iostream>
#include <string>
#include <random>

class PaperExecutionEngine : public ExecutionInterface {
private:
    double simulated_bankroll;

public:
    PaperExecutionEngine(double starting_bankroll) : simulated_bankroll(starting_bankroll) {
        std::cout << "[*] SHADOW MODE ENGAGED. Starting Simulated Bankroll: $" << simulated_bankroll << std::endl;
    }

    bool EstablishConnection() override {
        // Skips real API connection logic over external IP logic, boots instantly.
        std::cout << "[ OK ] Paper Trading Internal Execution Loop established." << std::endl;
        return true;
    }

    std::string ExecuteOrder(const std::string& target, double wager_amount, double odds) override {
        std::string mock_uuid = "SHADOW-" + std::to_string(rand() % 100000);
        
        std::cout << "\n[ SHADOW EXECUTION LOGGED ]" << std::endl;
        std::cout << "Target: " << target << " | Simulated Wager: $" << wager_amount << " | Odds: " << odds << std::endl;
        
        // Decrement simulated bankroll? Wait, Rust handles max bankroll, we just mock the ledger
        return mock_uuid;
    }

    void LogReceiptToTimescale(const std::string& execution_uuid) override {
        std::cout << "[*] Routing Simulated Execution Receipt " << execution_uuid << " to TimescaleDB..." << std::endl;
    }
};

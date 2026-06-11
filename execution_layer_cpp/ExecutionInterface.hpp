#pragma once
#include <string>
#include <vector>

// Abstract Base Class for Institutional Execution Layers
class ExecutionInterface {
public:
    virtual ~ExecutionInterface() = default;

    // Core Polymorphic Structuring Functions
    virtual bool EstablishConnection() = 0;
    virtual std::string ExecuteOrder(const std::string& target, double wager_amount, double odds) = 0;
    virtual void LogReceiptToTimescale(const std::string& execution_uuid) = 0;
};

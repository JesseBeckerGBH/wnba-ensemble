#include "PaperExecutionEngine.cpp"
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <target_string> <wager_amount> <odds>" << std::endl;
        return 1;
    }

    std::string target = argv[1];
    double wager_amount = std::stod(argv[2]);
    double odds = std::stod(argv[3]);

    // Instantiate with dummy initial bankroll since wager is calculated by Rust
    PaperExecutionEngine engine(1000.00); 
    engine.EstablishConnection();
    
    std::string uuid = engine.ExecuteOrder(target, wager_amount, odds);
    engine.LogReceiptToTimescale(uuid);

    return 0;
}

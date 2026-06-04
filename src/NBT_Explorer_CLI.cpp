#include <iostream>
#include <string>
#include <vector>

#include "NBT_Explorer.hpp"

int main() {
    NBTExplorer explorer;

    std::cout << "Booting up NBT Explorer..." << std::endl;

    if (!explorer.LoadWorld("../level.dat")) {
        std::cerr << "CRITICAL ERROR: Failed to load level.dat!" << std::endl;
        return 1;
    }

    // Start at the master "Data" folder
    auto currentFolder = explorer.GetMasterDataMap();

    if (!currentFolder) {
        std::cerr << "CRITICAL ERROR: Could not locate master Data map." << std::endl;
        return 1;
    }

    // THIS IS OUR BREADCRUMB TRAIL!
    // It stores a list of pointers to the folders we visited.
    std::vector<OptionalCompound> historyStack;

    std::cout << "Successfully jacked into the Matrix.\n";

    // The Menu Loop
    while (true) {
        std::cout << "\n[1] List all items in current folder" << std::endl;
        std::cout << "[2] Jump into a sub-folder (e.g., Player)" << std::endl;
        std::cout << "[3] Read a raw value (e.g., Time, GameType)" << std::endl;
        std::cout << "[4] Go Back (Up one level)" << std::endl;
        std::cout << "[5] Exit" << std::endl;
        std::cout << "System Override > ";

        int choice;
        std::cin >> choice;

        switch (choice) {
        case 1:
            NBTExplorer::PrintFolderContents(currentFolder);
            break;
        case 2: {
            std::cout << "Target folder name: ";
            std::string target;
            std::cin >> target;

            if (const auto nextFolder = NBTExplorer::EnterSubFolder(currentFolder, target)) {
                historyStack.push_back(currentFolder);
                currentFolder = nextFolder;
                std::cout << ">> Successfully jumped into '" << target << "'\n";
            }
            break;
        }
        case 3: {
            std::cout << "Target value name: ";
            std::string target;
            std::cin >> target;

            std::string rawValue = NBTExplorer::ReadRawValue(currentFolder, target);
            std::string valueType = NBTExplorer::GetValueType(currentFolder, target);

            std::cout << ">> " << target << " = " << rawValue << " (" << valueType << ")" << std::endl;

            break;
        }
        case 4:
            if (historyStack.empty()) {
                std::cout << "[!] You are already at the root level! You cannot go back further.\n";
            } else {
                currentFolder = historyStack.back();
                historyStack.pop_back();
                std::cout << ">> Moved back up one level.\n";
            }
            break;
        case 5:
            std::cout << "Disconnecting..." << std::endl;
            return 0;
        default:
            std::cout << "Invalid command." << std::endl;
            std::cin.clear();
            std::cin.ignore(10000, '\n');
            break;
        }
    }
}

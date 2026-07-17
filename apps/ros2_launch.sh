#!/bin/bash
# ============================================================
#  sniff_robot — ROS2 Launch Manager
#  Uruchamia pliki launch w działającym kontenerze Docker
# ============================================================

# ---- KONFIGURACJA (dostosuj do swojego projektu) ----
CONTAINER=$1                     # nazwa kontenera: sprawdź przez `docker ps`
PACKAGE="sniff_bringup"          # nazwa pakietu ROS2
LAUNCH_SEARCH_ROOT="/ros2_ws"    # gdzie szukać plików launch w kontenerze
# -----------------------------------------------------

# Kolory terminalu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

CURRENT_LAUNCH=""
LAUNCH_FILES=()

# ------------------------------------------------------------
# Sprawdź czy kontener działa
# ------------------------------------------------------------
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo -e "${RED}✗ Kontener '${CONTAINER}' nie jest uruchomiony!${NC}"
        echo -e "  Uruchom najpierw: ${CYAN}docker compose up -d${NC}"
        echo ""
        echo -e "  Dostępne kontenery:"
        docker ps --format '  • {{.Names}}\t({{.Status}})' 2>/dev/null || echo "  (brak działających)"
        echo ""
        exit 1
    fi
}

# ------------------------------------------------------------
# Pobierz listę plików launch z kontenera
# ------------------------------------------------------------
fetch_launches() {
    local launch_dir="${LAUNCH_SEARCH_ROOT}/install/${PACKAGE}/share/${PACKAGE}/launch"
    mapfile -t LAUNCH_FILES < <(
        docker exec "$CONTAINER" \
            find "$launch_dir" -maxdepth 1 -name '*launch.py' -printf '%f\n' \
            2>/dev/null \
        | sort -u
    )
}

# ------------------------------------------------------------
# Zatrzymaj aktywne procesy ros2 launch w kontenerze
# ------------------------------------------------------------
stop_all_launches() {
    # Najpierw SIGINT (graceful shutdown)
    docker exec "$CONTAINER" pkill -SIGINT -f "ros2 launch" 2>/dev/null || true
    sleep 0.8
    # Jeśli dalej żyje — SIGKILL
    docker exec "$CONTAINER" pkill -SIGKILL -f "ros2 launch" 2>/dev/null || true
    CURRENT_LAUNCH=""
}

# ------------------------------------------------------------
# Uruchom wybrany plik launch
# ------------------------------------------------------------
run_launch() {
    local launch_file="$1"

    # Zatrzymaj poprzedni launch jeśli jest aktywny
    if [ -n "$CURRENT_LAUNCH" ]; then
        echo -e "${YELLOW}⏹  Zatrzymuję: ${CURRENT_LAUNCH}${NC}"
        stop_all_launches
        sleep 0.3
    fi

    CURRENT_LAUNCH="$launch_file"

    echo -e "${GREEN}▶  Uruchamiam: ${launch_file}${NC}"
    echo -e "${DIM}   Ctrl+C → powrót do menu${NC}"
    echo -e "   ───────────────────────────────────────"

    # Uruchom launch w kontenerze (foreground).
    # Ctrl+C trafia do docker exec i zatrzymuje launch,
    # ale bash (trap '' INT) nie wychodzi ze skryptu.
    docker exec -it "$CONTAINER" bash -c \
        "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && exec ros2 launch $PACKAGE $launch_file"
    stty sane 2>/dev/null
    CURRENT_LAUNCH=""

    : '
    echo ""
    echo -e "${YELLOW}←  Powrót do menu${NC}"
    CURRENT_LAUNCH=""
    sleep 0.5
    '
}

# ------------------------------------------------------------
# Wyświetl menu główne
# ------------------------------------------------------------
show_menu() {
    clear
    echo -e "${BOLD}${BLUE}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║     🤖   sniff_robot — ROS2 Launcher      ║${NC}"
    echo -e "${BOLD}${BLUE}╚═══════════════════════════════════════════╝${NC}"

    # Status kontenera
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
        echo -e "  Kontener : ${GREEN}● działa${NC}  ${DIM}(${CONTAINER})${NC}"
    else
        echo -e "  Kontener : ${RED}✗ nie działa${NC}"
    fi

    # Aktywny launch
    if [ -n "$CURRENT_LAUNCH" ]; then
        echo -e "  Aktywny  : ${GREEN}▶ ${CURRENT_LAUNCH}${NC}"
    else
        echo -e "  Aktywny  : ${DIM}brak${NC}"
    fi
    echo ""

    # Lista launchów
    echo -e "  ${BOLD}Dostępne launche:${NC}"
    if [ ${#LAUNCH_FILES[@]} -eq 0 ]; then
        echo -e "  ${RED}⚠  Brak launchów — naciśnij 'r' żeby odświeżyć${NC}"
        echo -e "  ${DIM}   (szukam w: ${LAUNCH_SEARCH_ROOT}/src/${PACKAGE}/launch/)${NC}"
    else
        for i in "${!LAUNCH_FILES[@]}"; do
            local num=$((i + 1))
            if [ "${LAUNCH_FILES[$i]}" = "$CURRENT_LAUNCH" ]; then
                echo -e "  ${BOLD}${num})${NC} ${GREEN}▶ ${LAUNCH_FILES[$i]}${NC}"
            else
                echo -e "  ${BOLD}${num})${NC} ${LAUNCH_FILES[$i]}"
            fi
        done
    fi

    echo ""
    echo -e "  ${BOLD}Akcje:${NC}"
    echo -e "  ${BOLD}s)${NC}  Zatrzymaj aktywny launch"
    echo -e "  ${BOLD}r)${NC}  Odśwież listę launchów z kontenera"
    echo -e "  ${BOLD}q)${NC}  Wyjście"
    echo ""
}

# ------------------------------------------------------------
# Główna pętla
# ------------------------------------------------------------
main() {
    check_container
    fetch_launches

    # Ignoruj SIGINT w powłoce — Ctrl+C trafia do docker exec,
    # ale bash nie wychodzi ze skryptu i wraca do menu.
    trap '' INT

    while true; do
        show_menu

        local max=${#LAUNCH_FILES[@]}
        [ "$max" -eq 0 ] && max="?"
        read -rp "  Wybierz (1-${max} / s / r / q): " choice
        echo ""

        # Wybór numeryczny — uruchom launch
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            if [ "$choice" -ge 1 ] && [ "$choice" -le "${#LAUNCH_FILES[@]}" ]; then
                run_launch "${LAUNCH_FILES[$((choice - 1))]}"
            else
                echo -e "${RED}Numer poza zakresem (1-${#LAUNCH_FILES[@]})${NC}"
                sleep 1
            fi
            continue
        fi

        case "$choice" in
            s | S)
                if [ -n "$CURRENT_LAUNCH" ]; then
                    echo -e "${YELLOW}⏹  Zatrzymuję: ${CURRENT_LAUNCH}...${NC}"
                    stop_all_launches
                    echo -e "${GREEN}✓  Zatrzymano.${NC}"
                else
                    echo -e "${DIM}Brak aktywnego launcha.${NC}"
                fi
                sleep 1
                ;;
            r | R)
                echo -e "${CYAN}Odświeżam listę launchów...${NC}"
                fetch_launches
                if [ ${#LAUNCH_FILES[@]} -gt 0 ]; then
                    echo -e "${GREEN}✓  Znaleziono ${#LAUNCH_FILES[@]} plik(i/ów) launch.${NC}"
                else
                    echo -e "${RED}✗  Nie znaleziono żadnych plików launch.${NC}"
                fi
                sleep 1
                ;;
            q | Q)
                echo -e "${YELLOW}Zatrzymuję launche i wychodzę...${NC}"
                stop_all_launches
                echo -e "${GREEN}Do zobaczenia! 👋${NC}"
                trap - INT
                exit 0
                ;;
            "")
                # Puste wejście — np. po powrocie Ctrl+C z docker exec
                ;;
            *)
                echo -e "${RED}Nieznana opcja: '${choice}'${NC}"
                sleep 1
                ;;
        esac
    done
}

main

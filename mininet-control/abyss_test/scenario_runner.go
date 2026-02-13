package main

import (
	"fmt"
	"log"
	"os"
	"path"
	"strconv"
	"sync"
	"time"

	"github.com/kadmila/Abyss-Browser/abyss_core/ahost"
	"github.com/kadmila/Abyss-Browser/abyss_core/and"
)

// ScenarioRunner executes a sequence of actions defined in a scenario
type ScenarioRunner struct {
	contact_dir string
	time_start  int64
	time_end    int64
	scenario    []map[string]string
	host        *ahost.AbyssHost
	out_f       *os.File

	world_mtx sync.Mutex
	world     *and.World
}

// NewScenarioRunner creates a new ScenarioRunner with the given scenario and host
func NewScenarioRunner(contact_dir string, time_start int64, duration int64, scenario []map[string]string, host *ahost.AbyssHost, output_path string) *ScenarioRunner {
	out_f, err := os.Create(output_path)
	if err != nil {
		log.Fatalf("Error reading scenario file: %v", err)
	}
	return &ScenarioRunner{
		contact_dir: contact_dir,
		time_start:  time_start,
		time_end:    time_start + duration,
		scenario:    scenario,
		host:        host,
		out_f:       out_f,
	}
}

// Run executes the scenario by iterating over each step and waiting until the specified timestamp
func (sr *ScenarioRunner) Run() error {
	go sr.HandleEvents()

	for i, step := range sr.scenario {
		timeStr, ok := step["time"]
		if !ok {
			log.Printf("Warning: Step %d missing 'time' field, skipping", i)
			continue
		}

		timestamp, err := strconv.ParseInt(timeStr, 10, 64)
		if err != nil {
			log.Printf("Error: Step %d has invalid timestamp '%s': %v", i, timeStr, err)
			continue
		}

		target_timestamp := sr.time_start + timestamp
		if target_timestamp >= sr.time_end {
			break
		}

		targetTime := time.Unix(target_timestamp, 0)
		now := time.Now()

		if targetTime.After(now) {
			waitDuration := targetTime.Sub(now)
			time.Sleep(waitDuration)
		}

		// Action
		switch step["do"] {
		case "add":

			peer_id := step["id"]
			rc, err := os.ReadFile(path.Join(sr.contact_dir, peer_id+"_rc"))
			if err != nil {
				log.Fatalf("unable to read file: %v", err)
			}
			hs, err := os.ReadFile(path.Join(sr.contact_dir, peer_id+"_hs"))
			if err != nil {
				log.Fatalf("unable to read file: %v", err)
			}
			sr.host.AppendKnownPeer(string(rc), string(hs))

		case "dial":

			peer_id := step["id"]
			id_hash, err := os.ReadFile(path.Join(sr.contact_dir, peer_id+"_id"))
			if err != nil {
				log.Fatalf("unable to read file: %v", err)
			}
			sr.host.Dial(string(id_hash))

		case "join":

			peer_id := step["id"]
			id_hash, err := os.ReadFile(path.Join(sr.contact_dir, peer_id+"_id"))
			if err != nil {
				log.Fatalf("unable to read file: %v", err)
			}

			sr.world_mtx.Lock()
			if sr.world != nil {
				sr.host.CloseWorld(sr.world) // This automatically frees world path
				fmt.Fprintf(sr.out_f, "%d X %v\n", time.Now().UnixMilli(), sr.world.SessionID())
			}
			sr.world = nil
			sr.world_mtx.Unlock()

			for i := range 100 {
				if i == 99 {
					log.Println("Error: Failed to join. This is a failure.")
					break
				}

				sr.world_mtx.Lock()
				sr.world, err = sr.host.JoinWorld(string(id_hash), "/")
				sr.world_mtx.Unlock()

				if err == nil {
					break
				}
				time.Sleep(time.Millisecond * 100)
			}

		case "open":

			sr.world_mtx.Lock()
			if sr.world != nil {
				sr.host.CloseWorld(sr.world) // This automatically frees world path
				fmt.Fprintf(sr.out_f, "%d X %v\n", time.Now().UnixMilli(), sr.world.SessionID())
			}
			sr.world = sr.host.OpenWorld("https://www.example.com")
			sr.world_mtx.Unlock()

		}
	}

	targetTime := time.Unix(sr.time_end, 0)
	now := time.Now()

	if targetTime.After(now) {
		waitDuration := targetTime.Sub(now)
		time.Sleep(waitDuration)
	}

	sr.out_f.Close()
	return nil
}

func (sr *ScenarioRunner) HandleEvents() {
	event_ch := sr.host.GetEventCh()

	for {
		any_event, ok := <-event_ch
		if !ok {
			break
		}

		sr.world_mtx.Lock()

		switch event := any_event.(type) {
		case *and.EANDWorldEnter:

			if sr.world != nil && sr.world.SessionID() == event.World.SessionID() {
				sr.host.ExposeWorldForJoin(sr.world, "/") // this should not fail.
				fmt.Fprintf(sr.out_f, "%d E %v\n", time.Now().UnixMilli(), event.World.SessionID())
			}

		case *and.EANDSessionRequest:

			if sr.world != nil && sr.world.SessionID() == event.World.SessionID() {
				sr.host.AcceptWorldSession(sr.world, event.Peer.ID(), event.SessionID)
			}

		case *and.EANDSessionReady:

			if sr.world != nil && sr.world.SessionID() == event.World.SessionID() {
				fmt.Fprintf(sr.out_f, "%d J %v\n", time.Now().UnixMilli(), event.SessionID)
			}

		case *and.EANDSessionClose:

			if sr.world != nil && sr.world.SessionID() == event.World.SessionID() {
				fmt.Fprintf(sr.out_f, "%d L %v\n", time.Now().UnixMilli(), event.SessionID)
			}

		case *and.EANDObjectAppend:
		case *and.EANDObjectDelete:
		case *and.EANDWorldLeave: // join failure.

			if sr.world != nil && sr.world.SessionID() == event.World.SessionID() {
				sr.world = nil
				fmt.Fprintf(sr.out_f, "%d X %v\n", time.Now().UnixMilli(), event.World.SessionID())
			}
			// case *ahost.EPeerConnected:
			// 	fmt.Fprintf(sr.out_f, "%d Cn %v\n", time.Now().UnixMilli(), event.PeerID)
			// case *ahost.EPeerDisconnected:
			// 	fmt.Fprintf(sr.out_f, "%d Dc %v\n", time.Now().UnixMilli(), event.PeerID)
			// case *ahost.EPeerFound:
			// 	fmt.Fprintf(sr.out_f, "%d Fd %v\n", time.Now().UnixMilli(), event.PeerID)
			// case *ahost.EPeerForgot:
			// 	fmt.Fprintf(sr.out_f, "%d Fg %v\n", time.Now().UnixMilli(), event.PeerID)
		}

		sr.world_mtx.Unlock()
	}
}
